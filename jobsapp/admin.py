from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage

from jobsapp.models import Job, Applicant, JobImage, JobAlert, AdminAuditLog


class JobImageInline(admin.TabularInline):
    model = JobImage
    extra = 1


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "salary",
        "location",
        "type",
        "category",
        "company_name",
        "status",
        "last_date",
        "created_at",
        "filled",
        "user",
    ]
    list_filter = ["status", "salary", "last_date", "created_at", "user"]
    search_fields = ["title", "company_name", "location", "category"]
    date_hierarchy = "created_at"
    inlines = [JobImageInline]


@admin.register(JobImage)
class JobImageAdmin(admin.ModelAdmin):
    list_display = ["id", "job", "image", "caption", "created_at"]
    search_fields = ["job__title", "caption"]



@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "job", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["user__email", "user__first_name", "user__last_name", "job__title"]
    date_hierarchy = "created_at"


@admin.register(JobAlert)
class JobAlertAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "category", "location", "is_active", "user", "created_at"]
    list_filter = ["is_active", "category", "location", "created_at"]
    search_fields = ["email", "category", "location", "keywords"]
    date_hierarchy = "created_at"
    list_editable = ["is_active"]


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ["id", "action", "target_repr", "admin_user", "ip_address", "created_at"]
    list_filter = ["action", "created_at"]
    search_fields = ["action", "target_repr", "details", "ip_address", "admin_user__email"]
    date_hierarchy = "created_at"

