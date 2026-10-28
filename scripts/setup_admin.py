#!/usr/bin/env python
"""
Create or update administrative superuser account securely.
Credentials can be provided via environment variables:
  - DJANGO_SUPERUSER_EMAIL (default: wubantetilahun@gmail.com)
  - DJANGO_SUPERUSER_PASSWORD (default: prompt if interactive, or fallback to env)
  - DJANGO_SUPERUSER_FIRST_NAME (default: Admin)
  - DJANGO_SUPERUSER_LAST_NAME (default: User)
"""
import os
import sys
import getpass
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobs.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def setup_admin():
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "wubantetilahun@gmail.com")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
    first_name = os.environ.get("DJANGO_SUPERUSER_FIRST_NAME", "Wubante")
    last_name = os.environ.get("DJANGO_SUPERUSER_LAST_NAME", "Tilahun")

    if not password:
        if sys.stdin.isatty():
            password = getpass.getpass(f"Enter password for superuser [{email}]: ")
        else:
            print("ERROR: DJANGO_SUPERUSER_PASSWORD environment variable is required in non-interactive environments.")
            sys.exit(1)

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "role": "employer",
        },
    )

    user.first_name = first_name
    user.last_name = last_name
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.role = "employer"
    user.save()

    action = "Created new" if created else "Updated existing"
    print(f"[OK] {action} superuser account for: {email}")

if __name__ == "__main__":
    setup_admin()
