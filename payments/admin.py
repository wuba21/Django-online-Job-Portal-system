from django.contrib import admin
from .models import PaymentTransaction, SubscriptionPlan, UserSubscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "target_role", "price", "duration_days", "featured_jobs_count")
    list_filter = ("target_role",)
    search_fields = ("name",)


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "plan", "start_date", "end_date", "is_active")
    list_filter = ("is_active", "plan")
    search_fields = ("user__email",)


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "tx_ref", "user", "amount", "currency", "payment_method", "purpose", "status", "created_at")
    list_filter = ("status", "payment_method", "purpose", "created_at")
    search_fields = ("tx_ref", "user__email", "chapa_reference")
    date_hierarchy = "created_at"
