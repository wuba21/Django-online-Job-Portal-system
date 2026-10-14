import requests
from django.core.files.base import ContentFile
from django.utils import timezone


def update_user(backend, user, response, *args, **kwargs):
    """
    Social Auth pipeline step:
    1. Extracts full user profile from Google (first name, last name, avatar picture).
    2. Marks email verified with timestamp.
    3. Preserves admin privileges and creates company record if employer.
    """
    if backend.name == "google-oauth2":
        # 1. Verification flag
        user.is_verified = True
        if not user.email_verified_at:
            user.email_verified_at = timezone.now()

        # 2. Extract full name from Google response if missing
        first_name = response.get("given_name") or response.get("first_name", "")
        last_name = response.get("family_name") or response.get("last_name", "")

        if not user.first_name and first_name:
            user.first_name = first_name
        if not user.last_name and last_name:
            user.last_name = last_name

        # 3. Extract profile avatar picture from Google if not set
        picture_url = response.get("picture")
        if picture_url and not user.avatar:
            try:
                res = requests.get(picture_url, timeout=5)
                if res.status_code == 200:
                    filename = f"google_avatar_{user.id or 'temp'}.jpg"
                    user.avatar.save(filename, ContentFile(res.content), save=False)
            except Exception:
                pass

    # 4. Admin & Staff privilege preservation
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

    # 5. If employer, ensure company profile exists with full details
    if user.role == "employer":
        from accounts.models import Company
        company_name = f"{user.first_name} {user.last_name}".strip() or "My Company"
        Company.objects.get_or_create(user=user, defaults={"name": company_name})
