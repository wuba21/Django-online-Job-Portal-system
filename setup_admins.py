import os
import django

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobs.settings")
django.setup()

from accounts.models import User

# 1. Setup / Update wubante19@gmail.com
u1, created1 = User.objects.get_or_create(
    email="wubante19@gmail.com",
    defaults={
        "first_name": "Wubante",
        "last_name": "Admin",
        "role": "employer",
    },
)
u1.set_password("123456")
u1.is_staff = True
u1.is_superuser = True
u1.is_active = True
u1.role = "employer"
u1.save()

# 2. Setup / Update admin@admin.com
u2, created2 = User.objects.get_or_create(
    email="admin@admin.com",
    defaults={
        "first_name": "Admin",
        "last_name": "User",
        "role": "employer",
    },
)
u2.set_password("admin")
u2.is_staff = True
u2.is_superuser = True
u2.is_active = True
u2.role = "employer"
u2.save()

print("\n========================================")
print("SUCCESS: Admin accounts configured!")
print("Account 1: wubante19@gmail.com / 123456")
print("Account 2: admin@admin.com / admin")
print("========================================\n")
