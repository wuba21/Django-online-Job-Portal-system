import os
import django

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobs.settings")
django.setup()

from accounts.models import User

NEW_ADMIN_EMAIL = "wubantetilahun@gmail.com"
NEW_ADMIN_PASSWORD = "wuba@2121"

# 1. Setup / Update primary admin: wubantetilahun@gmail.com
u_primary, created = User.objects.get_or_create(
    email=NEW_ADMIN_EMAIL,
    defaults={
        "first_name": "Wubante",
        "last_name": "Tilahun",
        "role": "employer",
    },
)
u_primary.first_name = "Wubante"
u_primary.last_name = "Tilahun"
u_primary.set_password(NEW_ADMIN_PASSWORD)
u_primary.is_staff = True
u_primary.is_superuser = True
u_primary.is_active = True
u_primary.role = "employer"
u_primary.save()

# 2. Also update wubante19@gmail.com with the new password
try:
    u1 = User.objects.filter(email="wubante19@gmail.com").first()
    if u1:
        u1.set_password(NEW_ADMIN_PASSWORD)
        u1.is_staff = True
        u1.is_superuser = True
        u1.is_active = True
        u1.save()
except Exception as e:
    pass

# 3. Also update admin@admin.com as backup
try:
    u2 = User.objects.filter(email="admin@admin.com").first()
    if u2:
        u2.set_password(NEW_ADMIN_PASSWORD)
        u2.is_staff = True
        u2.is_superuser = True
        u2.is_active = True
        u2.save()
except Exception as e:
    pass

print("\n=======================================================")
print(" SUCCESS: Admin Account Configured!")
print(f" Admin Email   : {NEW_ADMIN_EMAIL}")
print(f" Admin Password: {NEW_ADMIN_PASSWORD}")
print(" Status        : Superuser & Staff (Active)")
print("=======================================================\n")
