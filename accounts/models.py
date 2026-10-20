from django.contrib.auth.models import AbstractUser
from django.db import models

from accounts.managers import UserManager

GENDER_CHOICES = [
    ("male", "Male"),
    ("female", "Female"),
]


class User(AbstractUser):
    username = None
    role = models.CharField(max_length=12, error_messages={"required": "Role must be provided"})
    gender = models.CharField(max_length=10, blank=True, null=True, default="", choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    email = models.EmailField(
        unique=True, blank=False, error_messages={"unique": "A user with that email already exists."}
    )
    is_vip = models.BooleanField(default=False, db_index=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __unicode__(self):
        return self.email

    def __str__(self):
        return self.email

    @property
    def is_employee(self):
        return self.role == "employee"

    @property
    def is_employer(self):
        return self.role == "employer"

    objects = UserManager()


class Company(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending Upload"),
        ("review", "Under AI Review"),
        ("verified", "Verified (Approved)"),
        ("rejected", "Rejected / Invalid"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="company")
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=150, blank=True, null=True)
    established_date = models.DateField(blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Banking, Tech, NGO, Construction")
    team_size = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. 1-10, 11-50, 50-200, 500+")
    cover_image = models.ImageField(upload_to="company_covers/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Ethiopian Business License & AI Verification Fields
    license_document = models.FileField(upload_to="company_licenses/", blank=True, null=True)
    tin_number = models.CharField(max_length=15, blank=True, null=True)
    license_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    license_ai_confidence = models.IntegerField(default=0)  # 0 to 100%
    license_rejection_reason = models.TextField(blank=True, null=True)
    license_verified_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def is_license_verified(self):
        return self.license_status == "verified"
