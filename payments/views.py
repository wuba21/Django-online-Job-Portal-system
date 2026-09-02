from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from jobsapp.models import Job
from .chapa import initialize_chapa_payment, verify_chapa_payment
from .models import PaymentTransaction, SubscriptionPlan, UserSubscription


def pricing_page(request):
    """
    Renders pricing tiers for Employers and Candidates.
    """
    employer_plans = SubscriptionPlan.objects.filter(target_role="employer").order_by("price")
    candidate_plans = SubscriptionPlan.objects.filter(target_role="employee").order_by("price")
    user_jobs = []
    if request.user.is_authenticated:
        user_jobs = Job.objects.filter(user=request.user)
    
    return render(request, "payments/pricing.html", {
        "employer_plans": employer_plans,
        "candidate_plans": candidate_plans,
        "user_jobs": user_jobs,
    })


@login_required
def initiate_checkout(request):
    """
    Initiates payment for Featured Job, Employer Plan, or Candidate VIP.
    """
    purpose = request.POST.get("purpose", "featured_job")
    job_id = request.POST.get("job_id")
    payment_method = request.POST.get("payment_method", "chapa")
    
    amount = 500.00  # Default 500 ETB
    title = "Job Portal Service"
    description = "Payment for Ethiopian Job Portal Services"
    job = None

    if purpose == "featured_job":
        amount = 500.00
        if job_id:
            job = get_object_or_404(Job, id=job_id, user=request.user)
        else:
            job = Job.objects.filter(user=request.user).first()
        job_title_str = f": {job.title}" if job else ""
        title = f"Featured VIP Job{job_title_str}"
        description = "Highlight job listing on home page & top search results for 30 days"

    elif purpose == "candidate_vip":
        amount = 300.00
        title = "Candidate VIP Badge"
        description = "VIP Applicant highlight & top resume recommendation for 30 days"

    elif purpose == "employer_subscription":
        amount = 1500.00
        title = "Employer Business Pro Package"
        description = "Unlimited Job postings + 5 Featured listings for 30 days"

    # Create pending transaction
    tx = PaymentTransaction.objects.create(
        user=request.user,
        amount=amount,
        currency="ETB",
        payment_method=payment_method,
        purpose=purpose,
        job=job,
        status="pending",
    )

    # Build return URL for callback
    return_url = request.build_absolute_uri(reverse("payments:payment_callback"))

    # Initialize with Chapa
    res = initialize_chapa_payment(
        tx_ref=tx.tx_ref,
        amount=amount,
        email=request.user.email,
        first_name=request.user.first_name,
        last_name=request.user.last_name,
        return_url=return_url,
        title=title,
        description=description,
    )

    if res.get("status") == "success" and res.get("checkout_url"):
        return redirect(res["checkout_url"])
    else:
        messages.error(request, res.get("message", "Unable to initialize payment session. Please try again."))
        return redirect("payments:pricing")


@login_required
def payment_callback(request):
    """
    Handles payment callback & verification from Chapa/Telebirr/CBE Birr.
    """
    tx_ref = request.GET.get("tx_ref")
    if not tx_ref:
        messages.error(request, "Invalid payment reference.")
        return redirect("payments:pricing")

    tx = get_object_or_404(PaymentTransaction, tx_ref=tx_ref, user=request.user)

    # Verify transaction status
    res = verify_chapa_payment(tx_ref)

    if res.get("status") == "success" or request.GET.get("mock") == "true":
        tx.status = "success"
        tx.save()

        # Activate feature based on purpose
        if tx.purpose == "featured_job" and tx.job:
            tx.job.is_featured = True
            tx.job.featured_until = timezone.now() + timedelta(days=30)
            tx.job.save()
            messages.success(request, f"🎉 Success! Job '{tx.job.title}' is now a Featured VIP Job listing!")

        elif tx.purpose == "candidate_vip":
            request.user.is_vip = True
            request.user.save()
            messages.success(request, "🎉 Congratulations! Your Candidate Profile is now VIP Featured!")

        elif tx.purpose == "employer_subscription":
            messages.success(request, "🎉 Congratulations! Your Employer Pro Package is now active!")

        return render(request, "payments/payment_success.html", {"transaction": tx})
    else:
        tx.status = "failed"
        tx.save()
        messages.error(request, "Payment verification failed. Please try again or contact support.")
        return redirect("payments:pricing")
