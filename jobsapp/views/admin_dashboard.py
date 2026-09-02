from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from datetime import timedelta

from accounts.models import User, Company
from jobsapp.models import Job, Applicant, APPLICANT_STATUS_CHOICES


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
        context["total_jobs"] = Job.objects.count()
        context["pending_jobs"] = Job.objects.filter(status="pending").count()
        context["approved_jobs"] = Job.objects.filter(status="approved").count()
        context["total_users"] = User.objects.count()
        context["users"] = User.objects.all().order_by("-date_joined")[:10]
        return context


@superuser_required
def approve_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    job.status = "approved"
    job.save()
    messages.success(request, f"Job '{job.title}' approved successfully.")
    return redirect("jobs:admin-dashboard")


@superuser_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    title = job.title
    job.delete()
    messages.success(request, f"Job '{title}' deleted.")
    return redirect("jobs:admin-dashboard")


@superuser_required
def toggle_user_active(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    status_text = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.email} {status_text}.")
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

    context = {
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
