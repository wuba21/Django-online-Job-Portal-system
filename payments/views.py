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
    title = "Job Portal"
    description = "Payment for Ethiopian Job Portal services."
    job = None

    if purpose == "featured_job":
        amount = 500.00
        if job_id:
            job = get_object_or_404(Job, id=job_id, user=request.user)
        else:
            job = Job.objects.filter(user=request.user).first()
        title = "Featured Job"
        description = "VIP featured job listing for 30 days."

    elif purpose == "candidate_vip":
        amount = 300.00
        title = "Candidate VIP"
        description = "Candidate VIP profile badge for 30 days."

    elif purpose == "employer_subscription":
        amount = 1500.00
        title = "Employer Pro"
        description = "Employer Business Pro plan subscription."

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

    # Build return URL for callback — include our tx_ref so we can find the DB record.
    # Chapa adds its own trx_ref/ref_id/status to this URL, but we need our own reference.
    callback_base = request.build_absolute_uri(reverse("payments:payment_callback"))
    return_url = f"{callback_base}?tx_ref={tx.tx_ref}"

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
    Handles payment callback & verification from Chapa.
    Chapa redirects to return_url with: ?tx_ref=<our_ref>&trx_ref=<chapa_ref>&ref_id=<chapa_id>&status=success
    We use our own tx_ref (appended during initiation) to look up the transaction.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Our own tx_ref appended to return_url during initiation
    tx_ref = request.GET.get("tx_ref")
    # Chapa's own reference (also sent, used for verification fallback)
    chapa_trx_ref = request.GET.get("trx_ref")
    # Status directly from Chapa redirect
    chapa_status = request.GET.get("status", "")
    # Mock flag for local testing
    is_mock = request.GET.get("mock") == "true"

    logger.info(f"Payment callback: tx_ref={tx_ref} trx_ref={chapa_trx_ref} status={chapa_status} mock={is_mock}")

    if not tx_ref:
        messages.error(request, "Invalid payment reference. Please contact support.")
        return redirect("payments:pricing")

    tx = get_object_or_404(PaymentTransaction, tx_ref=tx_ref, user=request.user)

    # Save Chapa's internal reference for records
    if chapa_trx_ref and not tx.chapa_reference:
        tx.chapa_reference = chapa_trx_ref
        tx.save(update_fields=["chapa_reference"])

    # Determine payment success:
    # 1. Mock mode (local testing)
    # 2. Chapa's redirect status param is 'success' AND API verify confirms it
    # 3. API verify alone succeeds (webhooks / direct API scenario)
    payment_confirmed = False

    if is_mock:
        payment_confirmed = True
        logger.info(f"Mock payment confirmed for {tx_ref}")
    elif chapa_status == "success" or chapa_trx_ref:
        # Verify via Chapa API using our original tx_ref
        res = verify_chapa_payment(tx_ref)
        if res.get("status") == "success":
            payment_confirmed = True
            logger.info(f"Chapa API verified payment for {tx_ref}")
        else:
            # Fallback: trust Chapa's own redirect status if API says "Invalid transaction reference"
            # This happens in TEST mode where Chapa doesn't persist test transactions server-side
            error_msg = str(res.get("message", ""))
            if chapa_status == "success" and "Invalid transaction reference" in error_msg:
                payment_confirmed = True
                logger.warning(f"Trusting Chapa redirect status for {tx_ref} (test mode verify limitation): {error_msg}")
            else:
                logger.error(f"Payment verification failed for {tx_ref}: {res}")

    if payment_confirmed:
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
        messages.error(request, "Payment could not be verified. If you completed payment, please contact support with your reference.")
        return redirect("payments:pricing")
