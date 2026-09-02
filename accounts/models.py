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
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="company")
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=150, blank=True, null=True)
    established_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
