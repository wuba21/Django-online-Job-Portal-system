import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


PAYMENT_METHOD_CHOICES = (
    ("chapa", "Chapa (Telebirr / CBE Birr / Card)"),
    ("telebirr", "Telebirr Direct"),
    ("cbe_birr", "CBE Birr Direct"),
)

PAYMENT_STATUS_CHOICES = (
    ("pending", "Pending"),
    ("success", "Success"),
    ("failed", "Failed"),
)

PURPOSE_CHOICES = (
    ("featured_job", "Featured Job Listing"),
    ("employer_subscription", "Employer Subscription Plan"),
    ("candidate_vip", "Candidate VIP Badge & Resume Boost"),
)


class SubscriptionPlan(models.Model):
    TARGET_ROLE_CHOICES = (
        ("employer", "Employer"),
        ("employee", "Candidate"),
    )

    name = models.CharField(max_length=100)
    target_role = models.CharField(max_length=20, choices=TARGET_ROLE_CHOICES, default="employer")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in ETB")
    duration_days = models.IntegerField(default=30)
    featured_jobs_count = models.IntegerField(default=0, help_text="Number of featured jobs included")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.target_role.title()}) - {self.price} ETB"


class UserSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def is_valid(self):
        return self.is_active and self.end_date >= timezone.now()

    def __str__(self):
        return f"{self.user.email} - {self.plan.name if self.plan else 'Custom'} ({'Active' if self.is_valid() else 'Expired'})"


class PaymentTransaction(models.Model):
    tx_ref = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="ETB")
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default="chapa")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending")
    purpose = models.CharField(max_length=50, choices=PURPOSE_CHOICES, default="featured_job")
    job = models.ForeignKey("jobsapp.Job", on_delete=models.SET_NULL, null=True, blank=True, related_name="payment_transactions")
    chapa_reference = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tx_ref} | {self.user.email} | {self.amount} {self.currency} | {self.status.upper()}"
