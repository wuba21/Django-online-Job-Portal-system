from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, TemplateView, View

from accounts.models import User, Company
from categories.models import Category
from jobsapp.models import Applicant, Job, Notification


def staff_or_superuser_required(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@method_decorator(user_passes_test(staff_or_superuser_required, login_url=reverse_lazy("accounts:login")), name="dispatch")
class AdminDashboardView(TemplateView):
    template_name = "jobs/admin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_users"] = User.objects.count()
        context["total_applicants"] = User.objects.filter(role="employee").count()
        context["total_employers"] = User.objects.filter(role="employer").count()
        context["total_jobs"] = Job.objects.count()
        context["active_jobs"] = Job.objects.filter(filled=False, status="approved").count()
        context["pending_jobs"] = Job.objects.filter(status="pending").count()
        context["total_applications"] = Applicant.objects.count()

        context["recent_jobs"] = Job.objects.select_related("user").all()[:10]
        context["recent_users"] = User.objects.all().order_by("-id")[:10]
        context["categories"] = Category.objects.all()
        return context


@user_passes_test(staff_or_superuser_required, login_url=reverse_lazy("accounts:login"))
def toggle_user_active(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, "Cannot deactivate superuser account.")
    else:
        user.is_active = not user.is_active
        user.save()
        status_str = "activated" if user.is_active else "deactivated"
        messages.success(request, f"User {user.email} successfully {status_str}.")
    return HttpResponseRedirect(reverse_lazy("jobs:admin-dashboard"))


@user_passes_test(staff_or_superuser_required, login_url=reverse_lazy("accounts:login"))
def approve_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    job.status = "approved"
    job.save()
    messages.success(request, f"Job '{job.title}' approved successfully.")
    return HttpResponseRedirect(reverse_lazy("jobs:admin-dashboard"))


@user_passes_test(staff_or_superuser_required, login_url=reverse_lazy("accounts:login"))
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    title = job.title
    job.delete()
    messages.success(request, f"Job '{title}' deleted successfully.")
    return HttpResponseRedirect(reverse_lazy("jobs:admin-dashboard"))
