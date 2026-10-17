from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def user_is_employer(function):
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        # Superusers/staff bypass role checks
        if request.user.is_superuser or request.user.is_staff:
            return function(request, *args, **kwargs)
        if request.user.role == "employer":
            # Allow access to profile update and license verification even if unverified
            from django.urls import reverse
            allowed_paths = [
                reverse("accounts:employer-verify-license"),
                reverse("accounts:employer-profile-update"),
            ]
            if any(request.path.startswith(p) for p in allowed_paths):
                return function(request, *args, **kwargs)

            # Check business license verification status for job operations
            company = getattr(request.user, "company", None)
            if not company or not company.is_license_verified:
                from django.contrib import messages
                messages.warning(
                    request,
                    "ህጋዊ የንግድ ፈቃድዎን እስኪያረጋግጡ ድረስ ስራ መለጠፍ አይችሉም። እባክዎ ፈቃድዎን እዚህ ያረጋግጡ።"
                )
                return redirect("accounts:employer-verify-license")
            return function(request, *args, **kwargs)
        raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def user_is_employee(function):
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        # Superusers, staff, and employees allowed
        if request.user.is_superuser or request.user.is_staff or request.user.role == "employee":
            return function(request, *args, **kwargs)
        from django.contrib import messages
        messages.warning(request, "Only candidate / job seeker accounts can submit applications.")
        job_id = kwargs.get("job_id")
        if job_id:
            return redirect("jobs:jobs-detail", id=job_id)
        return redirect("jobs:home")

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
