import csv
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q
from django.http import HttpResponse
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


def log_admin_action(request, action, target_repr, details=""):
    """
    Records an administrative action in the audit log for security & compliance.
    """
    try:
        from jobsapp.models import AdminAuditLog
        user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip:
            ip = ip.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        AdminAuditLog.objects.create(
            admin_user=user,
            action=action,
            target_repr=str(target_repr)[:255],
            details=details,
            ip_address=ip[:50] if ip else None
        )
    except Exception:
        pass


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
            # Notify matching Job Alert subscribers
            try:
                from jobsapp.views.home import send_job_alert_notifications
                send_job_alert_notifications(job, request=request)
            except Exception:
                pass
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
        log_admin_action(request, "PAYMENT_SUCCESS", f"Tx #{tx.id}: {tx.tx_ref} ({tx.amount} ETB)", details=f"User: {tx.user.email} | Purpose: {tx.purpose}")
        messages.success(request, f"Transaction {tx.tx_ref} marked SUCCESS and benefits applied!")

    elif new_status in ["failed", "pending"]:
        tx.status = new_status
        tx.save(update_fields=["status", "updated_at"])
        log_admin_action(request, f"PAYMENT_{new_status.upper()}", f"Tx #{tx.id}: {tx.tx_ref} ({tx.amount} ETB)", details=f"User: {tx.user.email}")
        messages.info(request, f"Transaction {tx.tx_ref} status set to {new_status.upper()}.")

    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("jobs:admin-payments-dashboard")


# ===========================================================================
# 3. Talent Search / Headhunting CV Bank
# ===========================================================================

@superuser_required
def admin_candidates_talent_pool(request):
    """
    Candidate Talent Bank & Headhunting Portal:
    Allows administrators to search, filter, and shortlist candidates across
    the entire database by skills, degree, experience, city, and CV availability.
    """
    candidates = (
        User.objects.filter(role="employee")
        .select_related("applicant_profile")
        .prefetch_related("skills", "educations", "experiences", "resume_cvs")
        .order_by("-date_joined")
    )

    # Filter metrics
    total_candidates = User.objects.filter(role="employee").count()
    vip_candidates_count = User.objects.filter(role="employee", is_vip=True).count()
    verified_candidates_count = User.objects.filter(role="employee", is_verified=True).count()
    candidates_with_cv = (
        User.objects.filter(role="employee")
        .filter(Q(applicant_profile__cv_file__isnull=False) | Q(resume_cvs__isnull=False))
        .distinct()
        .count()
    )

    # Filtering parameters
    query = request.GET.get("q", "").strip()
    if query:
        candidates = candidates.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(applicant_profile__title__icontains=query) |
            Q(applicant_profile__bio__icontains=query) |
            Q(skills__name__icontains=query) |
            Q(educations__degree__icontains=query) |
            Q(educations__field_of_study__icontains=query) |
            Q(experiences__title__icontains=query) |
            Q(experiences__company__icontains=query)
        ).distinct()

    location_filter = request.GET.get("location", "").strip()
    if location_filter and location_filter != "all":
        candidates = candidates.filter(applicant_profile__location__icontains=location_filter)

    skill_filter = request.GET.get("skill", "").strip()
    if skill_filter and skill_filter != "all":
        candidates = candidates.filter(skills__name__iexact=skill_filter).distinct()

    filter_type = request.GET.get("filter_type")
    if filter_type == "vip":
        candidates = candidates.filter(is_vip=True)
    elif filter_type == "verified":
        candidates = candidates.filter(is_verified=True)
    elif filter_type == "has_cv":
        candidates = candidates.filter(
            Q(applicant_profile__cv_file__isnull=False) | Q(resume_cvs__isnull=False)
        ).distinct()

    paginator = Paginator(candidates, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Available locations and common skills for filtering
    from jobsapp.models import CandidateSkill, ETHIOPIAN_LOCATIONS
    top_skills = (
        CandidateSkill.objects.values("name")
        .annotate(count=Count("id"))
        .order_by("-count")[:15]
    )

    from payments.models import PaymentTransaction
    pending_companies_count = Company.objects.filter(license_status__in=["pending", "review"]).count()
    pending_payments_count = PaymentTransaction.objects.filter(status="pending").count()

    context = {
        "active_tab": "candidates",
        "candidates": page_obj,
        "total_candidates": total_candidates,
        "vip_candidates_count": vip_candidates_count,
        "verified_candidates_count": verified_candidates_count,
        "candidates_with_cv": candidates_with_cv,
        "pending_companies_count": pending_companies_count,
        "pending_payments_count": pending_payments_count,
        "query": query,
        "location_filter": location_filter,
        "skill_filter": skill_filter,
        "filter_type": filter_type or "all",
        "top_skills": top_skills,
        "ethiopian_locations": [loc[0] for loc in ETHIOPIAN_LOCATIONS],
    }
    return render(request, "jobs/admin/candidates_talent_pool.html", context)


# ===========================================================================
# 4. Broadcast & Mass Communication Center
# ===========================================================================

@superuser_required
def admin_broadcast_announcements(request):
    """
    Mass Communication & Announcement Center:
    Broadcasts announcements to All Job Seekers, All Employers, or Everyone
    via In-App Notifications and styled HTML transactional Emails.
    """
    from payments.models import PaymentTransaction
    pending_companies_count = Company.objects.filter(license_status__in=["pending", "review"]).count()
    pending_payments_count = PaymentTransaction.objects.filter(status="pending").count()

    from jobsapp.models import AdminAuditLog
    recent_broadcasts = AdminAuditLog.objects.filter(action="BROADCAST_SENT").order_by("-created_at")[:10]

    if request.method == "POST":
        target = request.POST.get("target", "all")  # 'all', 'candidates', 'employers'
        channels = request.POST.getlist("channels")  # 'in_app', 'email'
        subject = request.POST.get("subject", "").strip()
        message_body = request.POST.get("message", "").strip()
        action_url = request.POST.get("action_url", "").strip()
        action_text = request.POST.get("action_text", "").strip() or "View Announcement"

        if not subject or not message_body:
            messages.error(request, "Please provide both an announcement title and message content.")
            return redirect("jobs:admin-broadcast")

        if not channels:
            channels = ["in_app"]

        # Determine audience queryset
        if target == "candidates":
            recipients = User.objects.filter(role="employee", is_active=True)
            audience_name = "All Job Seekers"
        elif target == "employers":
            recipients = User.objects.filter(role="employer", is_active=True)
            audience_name = "All Employers"
        elif target == "subscribers":
            from jobsapp.models import JobAlert
            recipients = []
            alert_emails = list(JobAlert.objects.filter(is_active=True).values_list("email", flat=True).distinct())
            audience_name = f"Job Alert Subscribers ({len(alert_emails)} Emails)"
        else:
            recipients = User.objects.filter(is_active=True)
            audience_name = "All Registered Users"

        recipient_count = len(alert_emails) if target == "subscribers" else recipients.count()
        in_app_count = 0
        email_count = 0

        # Deliver In-App Notifications in bulk
        if "in_app" in channels and target != "subscribers":
            from jobsapp.models import Notification
            notifications = [
                Notification(
                    user=u,
                    title=subject,
                    message=message_body[:500],
                    link=action_url if action_url else "/notifications/"
                )
                for u in recipients
            ]
            Notification.objects.bulk_create(notifications, batch_size=200)
            in_app_count = len(notifications)

        # Deliver Emails
        if "email" in channels:
            email_list = alert_emails if target == "subscribers" else [u.email for u in recipients if u.email]
            for em in email_list:
                try:
                    send_event_email(
                        user_email=em,
                        subject=subject,
                        message=message_body,
                        action_url=action_url or request.build_absolute_uri("/"),
                        action_text=action_text
                    )
                    email_count += 1
                except Exception:
                    pass

        # Log action in audit trail
        log_admin_action(
            request,
            action="BROADCAST_SENT",
            target_repr=f"Target: {audience_name} ({recipient_count} recipients)",
            details=f"Subject: {subject} | Channels: {', '.join(channels)} | In-app: {in_app_count}, Email: {email_count}"
        )

        messages.success(
            request,
            f"🎉 Broadcast successfully dispatched to {audience_name}! "
            f"({in_app_count} In-App Notifications delivered, {email_count} Emails sent)"
        )
        return redirect("jobs:admin-broadcast")

    from jobsapp.models import JobAlert
    total_candidates = User.objects.filter(role="employee").count()
    total_employers = User.objects.filter(role="employer").count()
    total_users = User.objects.count()
    total_subscribers = JobAlert.objects.filter(is_active=True).count()
    subscribers_list = JobAlert.objects.all().order_by("-created_at")[:15]

    context = {
        "active_tab": "broadcast",
        "pending_companies_count": pending_companies_count,
        "pending_payments_count": pending_payments_count,
        "total_candidates": total_candidates,
        "total_employers": total_employers,
        "total_users": total_users,
        "total_subscribers": total_subscribers,
        "subscribers_list": subscribers_list,
        "recent_broadcasts": recent_broadcasts,
    }
    return render(request, "jobs/admin/broadcast_center.html", context)


# ===========================================================================
# 5. Administrative Audit Logs & Moderator Activity Trail
# ===========================================================================

@superuser_required
def admin_audit_logs_view(request):
    """
    Displays complete chronological audit logs of all moderator actions:
    Job moderation, company license reviews, payment approvals, user status changes,
    and system broadcasts.
    """
    from jobsapp.models import AdminAuditLog
    from payments.models import PaymentTransaction

    logs = AdminAuditLog.objects.select_related("admin_user").all().order_by("-created_at")

    # Filters
    action_filter = request.GET.get("action", "").strip()
    if action_filter and action_filter != "all":
        logs = logs.filter(action=action_filter)

    query = request.GET.get("q", "").strip()
    if query:
        logs = logs.filter(
            Q(target_repr__icontains=query) |
            Q(details__icontains=query) |
            Q(admin_user__email__icontains=query)
        )

    paginator = Paginator(logs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    distinct_actions = AdminAuditLog.objects.values_list("action", flat=True).distinct()
    pending_companies_count = Company.objects.filter(license_status__in=["pending", "review"]).count()
    pending_payments_count = PaymentTransaction.objects.filter(status="pending").count()

    context = {
        "active_tab": "audit",
        "logs": page_obj,
        "distinct_actions": distinct_actions,
        "action_filter": action_filter or "all",
        "query": query,
        "total_logs_count": AdminAuditLog.objects.count(),
        "pending_companies_count": pending_companies_count,
        "pending_payments_count": pending_payments_count,
    }
    return render(request, "jobs/admin/audit_logs.html", context)


# ===========================================================================
# 6. Data Export (CSV / Excel Compatible)
# ===========================================================================

@superuser_required
def admin_export_candidates_csv(request):
    """
    Exports candidates database into Excel-compatible UTF-8 CSV.
    """
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="candidates_export.csv"'
    response.write("\ufeff")

    writer = csv.writer(response)
    writer.writerow([
        "Candidate ID", "First Name", "Last Name", "Email", "Phone", "Gender",
        "Professional Title", "Location", "VIP Candidate", "Verified", "Skills",
        "Highest Degree", "Recent Work Experience", "Date Registered"
    ])

    candidates = (
        User.objects.filter(role="employee")
        .select_related("applicant_profile")
        .prefetch_related("skills", "educations", "experiences")
        .order_by("-date_joined")
    )

    for c in candidates:
        profile = getattr(c, "applicant_profile", None)
        title = profile.title if profile else ""
        location = profile.location if profile else ""
        skills_str = ", ".join([s.name for s in c.skills.all()[:8]])
        edu = c.educations.first()
        edu_str = f"{edu.degree} ({edu.institution})" if edu else ""
        exp = c.experiences.first()
        exp_str = f"{exp.title} at {exp.company}" if exp else ""

        writer.writerow([
            c.id, c.first_name, c.last_name, c.email, c.phone_number or "",
            c.gender or "", title, location, "YES" if c.is_vip else "NO",
            "YES" if c.is_verified else "NO", skills_str, edu_str, exp_str,
            c.date_joined.strftime("%Y-%m-%d %H:%M")
        ])

    log_admin_action(request, "DATA_EXPORT", "Exported Candidates to CSV", details=f"Total: {candidates.count()}")
    return response


@superuser_required
def admin_export_jobs_csv(request):
    """
    Exports all platform jobs into Excel-compatible UTF-8 CSV.
    """
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="jobs_export.csv"'
    response.write("\ufeff")

    writer = csv.writer(response)
    writer.writerow([
        "Job ID", "Title", "Company Name", "Employer Email", "Location", "Category",
        "Job Type", "Experience Level", "Salary Min (ETB)", "Salary Max (ETB)",
        "Status", "VIP Featured", "Applications Count", "Date Posted", "Deadline"
    ])

    jobs = Job.objects.select_related("user", "company").prefetch_related("applicants").order_by("-created_at")

    for j in jobs:
        writer.writerow([
            j.id, j.title, j.company_name, j.user.email if j.user else "",
            j.location, j.category, j.type, j.experience_level,
            j.salary or "", j.salary_max or "", j.status.upper(),
            "YES" if j.is_featured else "NO", j.applicants.count(),
            j.created_at.strftime("%Y-%m-%d"), j.last_date.strftime("%Y-%m-%d") if j.last_date else ""
        ])

    log_admin_action(request, "DATA_EXPORT", "Exported Jobs to CSV", details=f"Total: {jobs.count()}")
    return response


@superuser_required
def admin_export_companies_csv(request):
    """
    Exports registered companies and license verification records to CSV.
    """
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="companies_export.csv"'
    response.write("\ufeff")

    writer = csv.writer(response)
    writer.writerow([
        "Company ID", "Company Name", "Employer Email", "TIN Number", "Location",
        "Website", "License Status", "AI Confidence Score (%)", "Has Document",
        "Rejection Reason", "Verified At", "Date Registered"
    ])

    companies = Company.objects.select_related("user").order_by("-created_at")

    for c in companies:
        writer.writerow([
            c.id, c.name, c.user.email if c.user else "", c.tin_number or "",
            c.location or "", c.website or "", c.license_status.upper(),
            c.license_ai_confidence, "YES" if c.license_document else "NO",
            c.license_rejection_reason or "",
            c.license_verified_at.strftime("%Y-%m-%d %H:%M") if c.license_verified_at else "",
            c.created_at.strftime("%Y-%m-%d")
        ])

    log_admin_action(request, "DATA_EXPORT", "Exported Companies to CSV", details=f"Total: {companies.count()}")
    return response


@superuser_required
def admin_export_payments_csv(request):
    """
    Exports complete financial ledger and transactions into Excel-compatible CSV.
    """
    from payments.models import PaymentTransaction
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="financial_transactions_export.csv"'
    response.write("\ufeff")

    writer = csv.writer(response)
    writer.writerow([
        "Transaction ID", "Internal Reference (tx_ref)", "Chapa Gateway Ref",
        "Customer Email", "Customer Role", "Amount (ETB)", "Method", "Purpose",
        "Status", "Associated Job", "Created Timestamp", "Updated Timestamp"
    ])

    transactions = PaymentTransaction.objects.select_related("user", "job").order_by("-created_at")

    for tx in transactions:
        writer.writerow([
            tx.id, tx.tx_ref, tx.chapa_reference or "",
            tx.user.email if tx.user else "", tx.user.role if tx.user else "",
            tx.amount, tx.payment_method, tx.purpose, tx.status.upper(),
            tx.job.title if tx.job else "",
            tx.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            tx.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        ])

    log_admin_action(request, "DATA_EXPORT", "Exported Financial Transactions to CSV", details=f"Total: {transactions.count()}")
    return response


@superuser_required
def admin_export_job_alerts_csv(request):
    """
    Exports all Job Alert email subscribers into Excel-compatible CSV.
    """
    from jobsapp.models import JobAlert
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="job_alert_subscribers_export.csv"'
    response.write("\ufeff")

    writer = csv.writer(response)
    writer.writerow([
        "Subscriber ID", "Email", "Target Category", "Target Location", "Keywords", "Status", "Subscribed Date"
    ])

    subscribers = JobAlert.objects.all().order_by("-created_at")

    for sub in subscribers:
        writer.writerow([
            sub.id,
            sub.email,
            sub.category or "All",
            sub.location or "All",
            sub.keywords or "N/A",
            "Active" if sub.is_active else "Inactive",
            sub.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])

    log_admin_action(request, "DATA_EXPORT", "Exported Job Alert Subscribers to CSV", details=f"Total: {subscribers.count()}")
    return response



