from django.utils import timezone


def update_user(backend, user, response, *args, **kwargs):
    """
    Social Auth pipeline step to set verified status, role, and preserve admin privileges.
    """
    # 1. When authenticated via Google, the email is genuinely verified by Google
    if backend.name == "google-oauth2":
        user.is_verified = True
        if not user.email_verified_at:
            user.email_verified_at = timezone.now()

    # 2. Admin & Staff privilege preservation
    admin_emails = ["wubantetilahun@gmail.com", "wubante19@gmail.com", "admin@admin.com"]
    if user.email in admin_emails or user.is_superuser:
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if not user.role:
            user.role = "employer"
    elif not user.role:
        # Default role for standard Google sign-ups
        user.role = "employee"

    user.is_active = True
    user.save()

    # 3. If employer, ensure company profile exists
    if user.role == "employer":
        from accounts.models import Company
        company_name = f"{user.first_name} {user.last_name}".strip() or "My Company"
        Company.objects.get_or_create(user=user, defaults={"name": company_name})
