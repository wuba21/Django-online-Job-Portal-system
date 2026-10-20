from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from datetime import timedelta

from accounts.models import User, Company
from jobsapp.models import Job, Applicant, APPLICANT_STATUS_CHOICES
from jobsapp.utils.notifications import create_notification, send_event_email


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.is_superuser, login_url="/accounts/login/")(view_func)


@method_decorator(superuser_required, name="dispatch")
class AdminDashboardView(ListView):
    model = Job
    template_name = "jobs/admin/dashboard.html"
    context_object_name = "jobs"
    paginate_by = 10

    def get_queryset(self):
        queryset = Job.objects.select_related("user", "company").all().order_by("-created_at")
        status_param = self.request.GET.get("status")
        if status_param in ["approved", "pending", "rejected"]:
            queryset = queryset.filter(status=status_param)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_users = User.objects.count()
        total_jobs = Job.objects.count()
        pending_jobs = Job.objects.filter(status="pending").count()
        approved_jobs = Job.objects.filter(status="approved").count()

        context["total_users"] = total_users
        context["total_applicants"] = User.objects.filter(role="employee").count()
        context["total_employers"] = User.objects.filter(role="employer").count()
        context["total_jobs"] = total_jobs
        context["active_jobs"] = approved_jobs
        context["pending_jobs"] = pending_jobs
        context["approved_jobs"] = approved_jobs
        context["total_applications"] = Applicant.objects.count()
        context["categories_count"] = Job.objects.values("category").distinct().count()

        # Navigation & Badges
        context["active_tab"] = "jobs"
        context["pending_companies_count"] = Company.objects.filter(license_status__in=["pending", "review"]).count()
        from payments.models import PaymentTransaction
        context["pending_payments_count"] = PaymentTransaction.objects.filter(status="pending").count()

        # Provide recent users and jobs under both variable names (users/recent_users, jobs/recent_jobs)
        recent_users = User.objects.all().order_by("-date_joined")[:25]
        recent_jobs = Job.objects.select_related("user", "company").all().order_by("-created_at")[:25]
        context["users"] = recent_users
        context["recent_users"] = recent_users
        context["recent_jobs"] = recent_jobs
        return context


@superuser_required
def approve_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    job.status = "approved"
    job.save()
    
    # Broadcast vacancy alert to Telegram Channel/Bot
    try:
        from jobsapp.utils.telegram import broadcast_job_to_telegram
        broadcast_job_to_telegram(job, request=request)
    except Exception:
        pass

    # Notify Job Owner
    if getattr(job, "user", None):
        create_notification(
            user=job.user,
            title=f"Job Approved: {job.title}",
            message=f"Congratulations! Your job listing '{job.title}' for {job.company_name} was approved by administrators and is now publicly live on the portal.",
            link=f"/jobs/{job.id}/"
        )
        if job.user.email:
            send_event_email(
                user_email=job.user.email,
                subject=f"✅ Job Approved: '{job.title}' is Now Live!",
                message=f"Hello,\n\nGreat news! Your job posting for '{job.title}' at {job.company_name} has been approved by administrators and is now publicly live on the portal. Candidates can now view and submit applications.\n\nBest regards,\nEthio Job Portal Team",
                action_url=request.build_absolute_uri(f"/jobs/{job.id}/"),
                action_text="View Live Job Listing"
            )

    messages.success(request, f"Job '{job.title}' approved successfully.")
    referer = request.META.get("HTTP_REFERER")
    if referer and ("jobs/" in referer or "platform-admin" in referer):
        return redirect(referer)
    return redirect("jobs:admin-dashboard")


@superuser_required
def set_job_status(request, job_id, status):
    job = get_object_or_404(Job, id=job_id)
    if status in ["approved", "pending", "rejected"]:
        job.status = status
        if status == "approved":
            try:
                from jobsapp.utils.telegram import broadcast_job_to_telegram
                broadcast_job_to_telegram(job, request=request)
            except Exception:
                pass
            if getattr(job, "user", None):
                create_notification(
                    user=job.user,
                    title=f"Job Approved: {job.title}",
                    message=f"Congratulations! Your job listing '{job.title}' for {job.company_name} has been approved and is now live on the portal.",
                    link=f"/jobs/{job.id}/"
                )
                if job.user.email:
                    send_event_email(
                        user_email=job.user.email,
                        subject=f"✅ Job Approved: '{job.title}' is Now Live!",
                        message=f"Hello,\n\nYour job listing '{job.title}' for {job.company_name} has been approved by administrators and is now active on the portal.\n\nBest regards,\nEthio Job Portal Team",
                        action_url=request.build_absolute_uri(f"/jobs/{job.id}/"),
                        action_text="View Live Job Listing"
                    )
        elif status == "rejected":
            if getattr(job, "user", None):
                create_notification(
                    user=job.user,
                    title=f"Job Listing Rejected: {job.title}",
                    message=f"Your job listing '{job.title}' for {job.company_name} was reviewed and rejected by administrators. Please update your post or contact support.",
                    link="/employer/dashboard/"
                )
                if job.user.email:
                    send_event_email(
                        user_email=job.user.email,
                        subject=f"Notice Regarding Your Job Listing '{job.title}'",
                        message=f"Hello,\n\nYour job listing '{job.title}' for {job.company_name} was reviewed by administrators and could not be approved at this time. Please check your employer dashboard and ensure all details follow our guidelines.\n\nBest regards,\nEthio Job Portal Team",
                        action_url=request.build_absolute_uri("/employer/dashboard/"),
                        action_text="Go to Employer Dashboard"
                    )
        job.save()
        messages.success(request, f"Job status changed to {status.upper()}.")
    elif status == "filled":
        job.filled = not job.filled
        job.save()
        messages.success(request, f"Job marked as {'FILLED' if job.filled else 'ACTIVE'}.")
    else:
        messages.warning(request, "Invalid job status.")
    
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("jobs:admin-dashboard")


@superuser_required
def toggle_job_featured(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    job.is_featured = not job.is_featured
    if job.is_featured:
        job.featured_until = timezone.now() + timedelta(days=30)
        messages.success(request, f"Job '{job.title}' is now VIP FEATURED on homepage.")
        if getattr(job, "user", None):
            create_notification(
                user=job.user,
                title=f"⭐ VIP Featured: {job.title}",
                message=f"Great news! Your job listing '{job.title}' is now VIP Featured on the homepage for the next 30 days.",
                link=f"/jobs/{job.id}/"
            )
            if job.user.email:
                send_event_email(
                    user_email=job.user.email,
                    subject=f"⭐ Your Job '{job.title}' is now VIP Featured!",
                    message=f"Hello,\n\nYour job listing '{job.title}' has been upgraded to VIP Featured status on the Ethio Job Portal homepage for the next 30 days.\n\nBest regards,\nEthio Job Portal Team",
                    action_url=request.build_absolute_uri(f"/jobs/{job.id}/"),
                    action_text="View on Homepage"
                )
    else:
        job.featured_until = None
        messages.info(request, f"Job '{job.title}' is no longer featured.")
    job.save()
    
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("jobs:admin-dashboard")



@superuser_required
def broadcast_job_telegram(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    try:
        from jobsapp.utils.telegram import broadcast_job_to_telegram
        ok, detail = broadcast_job_to_telegram(job, request=request, return_detail=True)
        if ok:
            messages.success(request, f"Job '{job.title}' successfully broadcast to Telegram Channel!")
        else:
            messages.error(request, f"Telegram Broadcast Failed: {detail}")
    except Exception as e:
        messages.error(request, f"Failed to broadcast to Telegram: {e}")
    
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("jobs:admin-dashboard")


@superuser_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    title = job.title
    job.delete()
    messages.success(request, f"Job '{title}' deleted.")
    referer = request.META.get("HTTP_REFERER")
    if referer and "jobs/" not in referer:
        return redirect(referer)
    return redirect("jobs:admin-dashboard")


@superuser_required
def toggle_user_active(request, user_id):
    from django.http import JsonResponse
    user = get_object_or_404(User, id=user_id)
    
    # Self-deactivation protection
    if user.id == request.user.id and user.is_active:
        msg = "You cannot deactivate your own active admin account."
        if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get("ajax"):
            return JsonResponse({"status": "error", "message": msg}, status=400)
        messages.warning(request, msg)
        return redirect("jobs:admin-dashboard")

    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    status_text = "activated" if user.is_active else "deactivated"
    msg = f"User {user.email} {status_text} successfully."
    
    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get("ajax"):
        return JsonResponse({
            "status": "success",
            "message": msg,
            "is_active": user.is_active,
            "status_text": "Active" if user.is_active else "Inactive",
            "action_text": "Deactivate" if user.is_active else "Activate",
            "btn_class": "btn-outline-danger" if user.is_active else "btn-outline-success",
            "badge_class": "badge-success" if user.is_active else "badge-danger",
            "user_id": user.id
        })
        
    messages.success(request, msg)
    return redirect("jobs:admin-dashboard")


@superuser_required
def bulk_toggle_users(request):
    if request.method == "POST":
        action = request.POST.get("action")  # 'deactivate' or 'activate'
        user_ids = request.POST.getlist("user_ids")
        if not user_ids:
            messages.warning(request, "No users selected. Please select at least one user.")
            return redirect("jobs:admin-dashboard")

        # Exclude self from bulk deactivation
        if action == "deactivate" and str(request.user.id) in user_ids:
            user_ids = [uid for uid in user_ids if uid != str(request.user.id)]
            messages.info(request, "Your current admin account was excluded from deactivation.")

        new_status = (action == "activate")
        updated_count = User.objects.filter(id__in=user_ids).update(is_active=new_status)
        
        action_word = "activated" if new_status else "deactivated"
        messages.success(request, f"Successfully {action_word} {updated_count} user account(s).")
    return redirect("jobs:admin-dashboard")


@superuser_required
def admin_analytics_dashboard(request):
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    total_users = User.objects.count()
    total_candidates = User.objects.filter(role="employee").count()
    total_employers = User.objects.filter(role="employer").count()
    total_companies = Company.objects.count()

    total_jobs = Job.objects.count()
    approved_jobs = Job.objects.filter(status="approved").count()
    pending_jobs = Job.objects.filter(status="pending").count()
    filled_jobs = Job.objects.filter(filled=True).count()

    total_applications = Applicant.objects.count()
    recent_applications_count = Applicant.objects.filter(created_at__gte=thirty_days_ago).count()

    status_map = dict(APPLICANT_STATUS_CHOICES)
    app_status_counts = (
        Applicant.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
    status_distribution = []
    for item in app_status_counts:
        status_name = status_map.get(item["status"], "Other")
        status_distribution.append({"status": status_name, "count": item["count"]})

    category_counts = (
        Job.objects.values("category")
        .annotate(count=Count("id"))
        .order_by("-count")[:6]
    )

    recent_users = User.objects.order_by("-date_joined")[:5]
    recent_jobs = Job.objects.select_related("user", "company").order_by("-created_at")[:5]

    from payments.models import PaymentTransaction
    pending_companies_count = Company.objects.filter(license_status__in=["pending", "review"]).count()
    pending_payments_count = PaymentTransaction.objects.filter(status="pending").count()

    context = {
        "active_tab": "analytics",
        "pending_companies_count": pending_companies_count,
        "pending_payments_count": pending_payments_count,
        "total_users": total_users,
        "total_candidates": total_candidates,
        "total_employers": total_employers,
        "total_companies": total_companies,
        "total_jobs": total_jobs,
        "approved_jobs": approved_jobs,
        "pending_jobs": pending_jobs,
        "filled_jobs": filled_jobs,
        "total_applications": total_applications,
        "recent_applications_count": recent_applications_count,
        "status_distribution": status_distribution,
        "category_counts": category_counts,
        "recent_users": recent_users,
        "recent_jobs": recent_jobs,
    }
    return render(request, "admin/admin_dashboard.html", context)


# ===========================================================================
# 1. Company License & TIN Verification Queue
# ===========================================================================

@superuser_required
def admin_companies_verification(request):
    """
    Dedicated verification queue for Ethiopian business licenses and TINs.
    Allows platform admins to review uploaded PDFs/images, inspect AI confidence,
    and approve or reject company registrations.
    """
    companies = Company.objects.select_related("user").all().order_by("-created_at")

    # Metrics
    total_companies = Company.objects.count()
    pending_companies_count = Company.objects.filter(license_status__in=["pending", "review"]).count()
    verified_companies_count = Company.objects.filter(license_status="verified").count()
    rejected_companies_count = Company.objects.filter(license_status="rejected").count()
    with_docs_count = Company.objects.exclude(license_document="").exclude(license_document__isnull=True).count()
    
    from payments.models import PaymentTransaction
    pending_payments_count = PaymentTransaction.objects.filter(status="pending").count()

    status_filter = request.GET.get("status")
    if status_filter in ["pending", "review", "verified", "rejected"]:
        companies = companies.filter(license_status=status_filter)
    elif status_filter == "has_doc":
        companies = companies.exclude(license_document="").exclude(license_document__isnull=True)

    query = request.GET.get("q", "").strip()
    if query:
        companies = companies.filter(
            Q(name__icontains=query) |
            Q(tin_number__icontains=query) |
            Q(user__email__icontains=query) |
            Q(location__icontains=query)
        )

    paginator = Paginator(companies, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "active_tab": "companies",
        "companies": page_obj,
        "total_companies": total_companies,
        "pending_companies_count": pending_companies_count,
        "verified_companies_count": verified_companies_count,
        "rejected_companies_count": rejected_companies_count,
        "with_docs_count": with_docs_count,
        "pending_payments_count": pending_payments_count,
        "status_filter": status_filter or "all",
        "query": query,
    }
    return render(request, "jobs/admin/companies_verification.html", context)


@superuser_required
def admin_verify_company(request, company_id):
    """
    Approves and verifies a company's business license.
    Marks company and employer user as verified, sends in-app notification and email.
    """
    company = get_object_or_404(Company, id=company_id)
    company.license_status = "verified"
    company.license_verified_at = timezone.now()
    company.license_rejection_reason = ""
    company.save()

    if getattr(company, "user", None):
        company.user.is_verified = True
        company.user.save(update_fields=["is_verified"])
        create_notification(
            user=company.user,
            title="✅ Business License Verified!",
            message=f"Congratulations! The trade license and TIN for '{company.name}' have been verified by platform administrators. Your employer account now displays the official Verified badge.",
            link="/employer/dashboard/"
        )
        if company.user.email:
            send_event_email(
                user_email=company.user.email,
                subject=f"✅ Business License Verified: {company.name} is Verified!",
                message=f"Hello,\n\nGreat news! Your Ethiopian Business License and TIN for '{company.name}' have been reviewed and approved by platform administrators.\n\nYour job postings will now display the verified employer badge to build high trust with candidates.\n\nBest regards,\nEthio Job Portal Team",
                action_url=request.build_absolute_uri("/employer/dashboard/"),
                action_text="Go to Employer Dashboard"
            )

    messages.success(request, f"Company '{company.name}' successfully verified!")
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("jobs:admin-companies-verification")


@superuser_required
def admin_reject_company(request, company_id):
    """
    Rejects a company's business license submission with an actionable reason.
    """
    company = get_object_or_404(Company, id=company_id)
    reason = request.POST.get("rejection_reason", "").strip() or request.GET.get("reason", "").strip()
    if not reason:
        reason = "The uploaded business license or TIN could not be verified against government records. Please re-upload a clear, valid official copy."

    company.license_status = "rejected"
    company.license_rejection_reason = reason
    company.save()

    if getattr(company, "user", None):
        company.user.is_verified = False
        company.user.save(update_fields=["is_verified"])
        create_notification(
            user=company.user,
            title="⚠️ Trade License Verification Issue",
            message=f"The trade license verification for '{company.name}' was rejected: {reason}. Please re-upload a valid document.",
            link="/accounts/employer/verify-license/"
        )
        if company.user.email:
            send_event_email(
                user_email=company.user.email,
                subject=f"Action Required: Business License Verification for {company.name}",
                message=f"Hello,\n\nYour trade license submission for '{company.name}' could not be approved at this time.\n\nReason: {reason}\n\nPlease visit your dashboard to upload a new, clear copy of your valid trade license.\n\nBest regards,\nEthio Job Portal Team",
                action_url=request.build_absolute_uri("/accounts/employer/verify-license/"),
                action_text="Re-upload License"
            )

    messages.warning(request, f"Company '{company.name}' verification was rejected.")
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("jobs:admin-companies-verification")


@superuser_required
def admin_rerun_ai_verification(request, company_id):
    """
    Re-runs the Ethiopian government AI verification pipeline on the company's uploaded document.
    """
    company = get_object_or_404(Company, id=company_id)
    if not company.license_document:
        messages.error(request, f"No document uploaded for '{company.name}' to analyze.")
    else:
        try:
            from accounts.license_validator import verify_ethiopian_business_license
            result = verify_ethiopian_business_license(
                company.license_document,
                tin_input=company.tin_number,
                company_name=company.name
            )
            company.license_ai_confidence = result.get("confidence", 0)
            if result.get("tin_number") and not company.tin_number:
                company.tin_number = result["tin_number"]
            company.save()
            reasons_summary = " | ".join(result.get("reasons", [])) or "Analysis complete."
            messages.info(request, f"AI Analysis for '{company.name}': Confidence {company.license_ai_confidence}% ({reasons_summary})")
        except Exception as e:
            messages.error(request, f"AI verification analysis failed: {e}")

    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("jobs:admin-companies-verification")


# ===========================================================================
# 2. Payments & Financial Revenue Dashboard
# ===========================================================================

@superuser_required
def admin_payments_dashboard(request):
    """
    Executive financial control center: Tracks Chapa, Telebirr, and CBE Birr
    transactions, computes ETB revenue metrics, and manages VIP subscriptions.
    """
    from payments.models import PaymentTransaction, SubscriptionPlan, UserSubscription

    transactions = PaymentTransaction.objects.select_related("user", "job").all().order_by("-created_at")

    # Financial KPIs
    total_revenue = PaymentTransaction.objects.filter(status="success").aggregate(total=Sum("amount"))["total"] or 0
    
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_revenue = PaymentTransaction.objects.filter(
        status="success", created_at__gte=start_of_month
    ).aggregate(total=Sum("amount"))["total"] or 0

    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_revenue = PaymentTransaction.objects.filter(
        status="success", created_at__gte=start_of_today
    ).aggregate(total=Sum("amount"))["total"] or 0

    success_count = PaymentTransaction.objects.filter(status="success").count()
    pending_payments_count = PaymentTransaction.objects.filter(status="pending").count()
    failed_count = PaymentTransaction.objects.filter(status="failed").count()
    total_tx_count = PaymentTransaction.objects.count()

    active_subscriptions_count = UserSubscription.objects.filter(is_active=True, end_date__gte=now).count()
    pending_companies_count = Company.objects.filter(license_status__in=["pending", "review"]).count()

    # Filtering
    status_filter = request.GET.get("status")
    if status_filter in ["success", "pending", "failed"]:
        transactions = transactions.filter(status=status_filter)

    method_filter = request.GET.get("method")
    if method_filter in ["chapa", "telebirr", "cbe_birr"]:
        transactions = transactions.filter(payment_method=method_filter)

    purpose_filter = request.GET.get("purpose")
    if purpose_filter in ["featured_job", "employer_subscription", "candidate_vip"]:
        transactions = transactions.filter(purpose=purpose_filter)

    query = request.GET.get("q", "").strip()
    if query:
        transactions = transactions.filter(
            Q(tx_ref__icontains=query) |
            Q(chapa_reference__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )

    paginator = Paginator(transactions, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    recent_subscriptions = UserSubscription.objects.select_related("user", "plan").order_by("-start_date")[:8]
    plans = SubscriptionPlan.objects.all().order_by("price")

    context = {
        "active_tab": "payments",
        "transactions": page_obj,
        "total_revenue": total_revenue,
        "month_revenue": month_revenue,
        "today_revenue": today_revenue,
        "success_count": success_count,
        "pending_payments_count": pending_payments_count,
        "failed_count": failed_count,
        "total_tx_count": total_tx_count,
        "active_subscriptions_count": active_subscriptions_count,
        "pending_companies_count": pending_companies_count,
        "recent_subscriptions": recent_subscriptions,
        "plans": plans,
        "status_filter": status_filter or "all",
        "method_filter": method_filter or "all",
        "purpose_filter": purpose_filter or "all",
        "query": query,
    }
    return render(request, "jobs/admin/payments_dashboard.html", context)


@superuser_required
def admin_update_payment_status(request, tx_id):
    """
    Manually overrides or confirms a transaction status.
    When set to 'success', automatically fulfills user benefits:
    - Features the Job for 30 days
    - Activates Candidate VIP badge
    - Creates or extends Employer Subscription
    """
    from payments.models import PaymentTransaction, SubscriptionPlan, UserSubscription
    tx = get_object_or_404(PaymentTransaction, id=tx_id)
    new_status = request.POST.get("status") or request.GET.get("status")

    if new_status == "success":
        tx.status = "success"
        tx.save(update_fields=["status", "updated_at"])

        # Automatically apply fulfillment
        if tx.purpose == "featured_job" and tx.job:
            tx.job.is_featured = True
            tx.job.featured_until = timezone.now() + timedelta(days=30)
            tx.job.save(update_fields=["is_featured", "featured_until"])
            create_notification(
                user=tx.user,
                title="⭐ Job Featured Active!",
                message=f"Your payment of {tx.amount} ETB was confirmed. Job '{tx.job.title}' is now VIP Featured for 30 days!",
                link=f"/jobs/{tx.job.id}/"
            )
        elif tx.purpose in ["candidate_vip", "vip_candidate"]:
            tx.user.is_vip = True
            tx.user.save(update_fields=["is_vip"])
            create_notification(
                user=tx.user,
                title="⭐ VIP Candidate Badge Active!",
                message=f"Your payment of {tx.amount} ETB was confirmed. You now have a VIP Candidate profile badge for 30 days!",
                link="/employee/dashboard/"
            )
        elif tx.purpose == "employer_subscription":
            plan = SubscriptionPlan.objects.filter(target_role="employer").first()
            UserSubscription.objects.create(
                user=tx.user,
                plan=plan,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=30),
                is_active=True
            )
            create_notification(
                user=tx.user,
                title="💼 Employer Pro Subscription Active!",
                message=f"Your payment of {tx.amount} ETB was confirmed. Your Business Pro subscription is active for 30 days!",
                link="/employer/dashboard/"
            )

        if tx.user.email:
            send_event_email(
                user_email=tx.user.email,
                subject=f"Receipt: Payment Confirmed ({tx.amount} ETB) - Ethio Job Portal",
                message=f"Hello {tx.user.get_full_name() or 'Valued Customer'},\n\nYour payment of {tx.amount} ETB (Ref: {tx.tx_ref}) has been confirmed and your platform benefits have been activated.\n\nThank you for choosing Ethio Job Portal!\n\nBest regards,\nEthio Job Portal Team",
                action_url=request.build_absolute_uri("/"),
                action_text="Visit Platform"
            )
        messages.success(request, f"Transaction {tx.tx_ref} marked SUCCESS and benefits applied!")

    elif new_status in ["failed", "pending"]:
        tx.status = new_status
        tx.save(update_fields=["status", "updated_at"])
        messages.info(request, f"Transaction {tx.tx_ref} status set to {new_status.upper()}.")

    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("jobs:admin-payments-dashboard")

