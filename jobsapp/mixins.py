from django.contrib.auth.mixins import AccessMixin


class EmployeeRequiredMixin(AccessMixin):
    """Verify that the current user is employee, staff, or superuser."""

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
        if user.is_superuser or user.is_staff or user.role == "employee":
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


class EmployerRequiredMixin(AccessMixin):
    """Verify that the current user is employer, staff, or superuser."""

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
        if user.is_superuser or user.is_staff or user.role == "employer":
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()
