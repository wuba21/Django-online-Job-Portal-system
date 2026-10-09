def update_user(backend, user, response, *args, **kwargs):
    """
    Social Auth pipeline step to set roles and preserve admin status.
    """
    admin_emails = ["wubante19@gmail.com", "admin@admin.com"]
    if user.email in admin_emails or user.is_superuser:
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if not user.role:
            user.role = "employer"
    elif not user.role:
        user.role = "employee"
    user.save()
