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
            return function(request, *args, **kwargs)
        raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap


def user_is_employee(function):
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        # Superusers/staff bypass role checks
        if request.user.is_superuser or request.user.is_staff:
            return function(request, *args, **kwargs)
        if request.user.role == "employee":
            return function(request, *args, **kwargs)
        raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
