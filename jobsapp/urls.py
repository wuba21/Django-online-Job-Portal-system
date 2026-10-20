from django.urls import include, path

from jobsapp.views.admin_dashboard import (
    AdminDashboardView, admin_analytics_dashboard, approve_job, delete_job, toggle_user_active,
    bulk_toggle_users, set_job_status, toggle_job_featured, broadcast_job_telegram,
    admin_companies_verification, admin_verify_company, admin_reject_company, admin_rerun_ai_verification,
    admin_payments_dashboard, admin_update_payment_status,
    admin_candidates_talent_pool, admin_broadcast_announcements, admin_audit_logs_view,
    admin_export_candidates_csv, admin_export_jobs_csv, admin_export_companies_csv, admin_export_payments_csv,
    admin_export_job_alerts_csv
)
from jobsapp.views.employee import (
    ApplicantDashboardView, EditProfileView, EmployeeMyJobsListView, FavoriteListView,
    add_education, add_experience, add_skill, delete_education, delete_experience, delete_skill,
    mark_all_notifications_as_read, mark_notification_as_read, notifications_view, withdraw_application,
    ai_parse_resume
)
from jobsapp.views.employer import (
    ApplicantPerJobView, ApplicantsListView, AppliedApplicantView, DashboardView,
    EmployerProfileEditView, JobCreateView, JobUpdateView, SendResponseView, delete_employer_job, filled,
    export_applicants_csv, schedule_interview, quick_update_applicant_status
)
from jobsapp.views.company import CompanyDetailView, CompanyListView, add_company_review
from jobsapp.views.messages import inbox_view, start_conversation
from jobsapp.views.telegram_webapp import telegram_webapp_view
from jobsapp.views.home import (
    AboutUsView, ApplyJobView, HomeView, JobDetailsView, JobListView, SearchView, SalaryCalculatorView,
    create_job_alert, favorite
)

app_name = "jobs"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("favorite/", favorite, name="favorite"),
    path("search/", SearchView.as_view(), name="search"),
    path("salary-calculator/", SalaryCalculatorView.as_view(), name="salary-calculator"),
    path("job-alert/subscribe/", create_job_alert, name="create-job-alert"),

    # Public Company Directory & Reviews
    path("companies/", CompanyListView.as_view(), name="companies-list"),
    path("companies/<int:id>/", CompanyDetailView.as_view(), name="company-detail"),
    path("companies/<int:company_id>/review/", add_company_review, name="add-company-review"),

    # Direct 2-Way Candidate <-> Employer Messaging
    path("messages/", inbox_view, name="inbox"),
    path("messages/start/<int:candidate_id>/", start_conversation, name="start-conversation"),

    # AI Resume Auto-Profile Extractor
    path("profile/ai-parse-resume/", ai_parse_resume, name="ai-parse-resume"),

    # Telegram Mini-App (TMA) Portal
    path("telegram/app/", telegram_webapp_view, name="telegram-webapp"),

    # Notifications
    path("notifications/", notifications_view, name="notifications"),
    path("notifications/read/<int:pk>/", mark_notification_as_read, name="mark-notification-read"),
    path("notifications/read-all/", mark_all_notifications_as_read, name="mark-all-notifications-read"),

    # Employer Portal
    path(
        "employer/dashboard/",
        include(
            [
                path("", DashboardView.as_view(), name="employer-dashboard"),
                path("all-applicants/", ApplicantsListView.as_view(), name="employer-all-applicants"),
                path("applicants/<int:job_id>/", ApplicantPerJobView.as_view(), name="employer-dashboard-applicants"),
                path("applicants/<int:job_id>/export/", export_applicants_csv, name="export-applicants-csv"),
                path(
                    "applied-applicant/<int:job_id>/view/<int:applicant_id>",
                    AppliedApplicantView.as_view(),
                    name="applied-applicant-view",
                ),
                path("mark-filled/<int:job_id>/", filled, name="job-mark-filled"),
                path("delete-job/<int:job_id>/", delete_employer_job, name="employer-job-delete"),
                path("send-response/<int:applicant_id>", SendResponseView.as_view(), name="applicant-send-response"),
                path("schedule-interview/<int:applicant_id>/", schedule_interview, name="schedule-interview"),
                path("update-status/<int:applicant_id>/<int:status_id>/", quick_update_applicant_status, name="quick-update-status"),
                path("jobs/create/", JobCreateView.as_view(), name="employer-jobs-create"),
                path("jobs/<int:id>/edit/", JobUpdateView.as_view(), name="employer-jobs-edit"),
            ]
        ),
    ),

    # Applicant Portal
    path(
        "employee/",
        include(
            [
                path("dashboard/", ApplicantDashboardView.as_view(), name="applicant-dashboard"),
                path("my-applications", EmployeeMyJobsListView.as_view(), name="employee-my-applications"),
                path("withdraw-application/<int:applicant_id>/", withdraw_application, name="withdraw-application"),
                path("favorites", FavoriteListView.as_view(), name="employee-favorites"),
                path("education/add/", add_education, name="add-education"),
                path("education/delete/<int:pk>/", delete_education, name="delete-education"),
                path("experience/add/", add_experience, name="add-experience"),
                path("experience/delete/<int:pk>/", delete_experience, name="delete-experience"),
                path("skill/add/", add_skill, name="add-skill"),
                path("skill/delete/<int:pk>/", delete_skill, name="delete-skill"),
            ]
        ),
    ),
    # Root level aliases for profile actions
    path("education/add/", add_education, name="root-add-education"),
    path("education/delete/<int:pk>/", delete_education, name="root-delete-education"),
    path("experience/add/", add_experience, name="root-add-experience"),
    path("experience/delete/<int:pk>/", delete_experience, name="root-delete-experience"),
    path("skill/add/", add_skill, name="root-add-skill"),
    path("skill/delete/<int:pk>/", delete_skill, name="root-delete-skill"),

    # Custom Platform Admin Dashboard & Analytics
    path("platform-admin/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("analytics-dashboard/", admin_analytics_dashboard, name="admin-analytics-dashboard"),
    path("platform-admin/toggle-user/<int:user_id>/", toggle_user_active, name="admin-toggle-user"),
    path("platform-admin/bulk-toggle-users/", bulk_toggle_users, name="admin-bulk-toggle-users"),
    path("platform-admin/approve-job/<int:job_id>/", approve_job, name="admin-approve-job"),
    path("platform-admin/set-status/<int:job_id>/<str:status>/", set_job_status, name="admin-set-job-status"),
    path("platform-admin/toggle-featured/<int:job_id>/", toggle_job_featured, name="admin-toggle-featured"),
    path("platform-admin/broadcast-telegram/<int:job_id>/", broadcast_job_telegram, name="admin-broadcast-telegram"),
    path("platform-admin/delete-job/<int:job_id>/", delete_job, name="admin-delete-job"),

    # Admin: Ethiopian Business License & TIN Verification Queue
    path("platform-admin/companies/", admin_companies_verification, name="admin-companies-verification"),
    path("platform-admin/companies/<int:company_id>/verify/", admin_verify_company, name="admin-verify-company"),
    path("platform-admin/companies/<int:company_id>/reject/", admin_reject_company, name="admin-reject-company"),
    path("platform-admin/companies/<int:company_id>/ai-rescan/", admin_rerun_ai_verification, name="admin-rerun-ai-verification"),

    # Admin: Payments & Revenue Management
    path("platform-admin/payments/", admin_payments_dashboard, name="admin-payments-dashboard"),
    path("platform-admin/payments/<int:tx_id>/status/", admin_update_payment_status, name="admin-update-payment-status"),

    # Admin: Talent Search / Headhunting CV Bank
    path("platform-admin/candidates/", admin_candidates_talent_pool, name="admin-candidates-pool"),

    # Admin: Mass Broadcast & Announcements Center
    path("platform-admin/broadcast/", admin_broadcast_announcements, name="admin-broadcast"),

    # Admin: Security & Compliance Audit Logs
    path("platform-admin/audit-logs/", admin_audit_logs_view, name="admin-audit-logs"),

    # Admin: Excel/CSV Data Exports
    path("platform-admin/export/candidates/", admin_export_candidates_csv, name="admin-export-candidates-csv"),
    path("platform-admin/export/jobs/", admin_export_jobs_csv, name="admin-export-jobs-csv"),
    path("platform-admin/export/companies/", admin_export_companies_csv, name="admin-export-companies-csv"),
    path("platform-admin/export/payments/", admin_export_payments_csv, name="admin-export-payments-csv"),
    path("platform-admin/export/subscribers/", admin_export_job_alerts_csv, name="admin-export-alerts-csv"),

    # Public Job Pages
    path("apply-job/<int:job_id>/", ApplyJobView.as_view(), name="apply-job"),
    path("jobs/", JobListView.as_view(), name="jobs"),
    path("jobs/<int:id>/", JobDetailsView.as_view(), name="jobs-detail"),
    path("jobs/<slug:slug>/", JobDetailsView.as_view(), name="jobs-detail-slug"),
    path("about-us/", AboutUsView.as_view(), name="about-us"),
]
