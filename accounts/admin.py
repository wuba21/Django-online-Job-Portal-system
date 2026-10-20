from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Company


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "role",
        "gender",
        "phone_number",
        "is_active",
        "is_vip",
        "is_staff",
        "date_joined",
    )
    list_filter = ("role", "gender", "is_active", "is_vip", "is_staff", "date_joined")
    search_fields = ("email", "first_name", "last_name", "phone_number")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "gender", "phone_number", "avatar", "bio")},
        ),
        (
            "Permissions & Role",
            {"fields": ("role", "is_vip", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "role", "password1", "password2"),
            },
        ),
    )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "location", "license_status", "created_at")
    search_fields = ("name", "location", "user__email", "tin_number")
    list_filter = ("license_status", "created_at")


from .models import CompanyReview


@admin.register(CompanyReview)
class CompanyReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "company", "user", "rating", "title", "is_approved", "created_at")
    list_filter = ("rating", "is_approved", "created_at")
    search_fields = ("company__name", "user__email", "title", "review_text")
    actions = ["approve_reviews", "unapprove_reviews"]

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected company reviews"

    def unapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    unapprove_reviews.short_description = "Hide/Unapprove selected company reviews"
