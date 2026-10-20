from django.urls import include, path

from jobsapp.views.admin_dashboard import (
    AdminDashboardView, admin_analytics_dashboard, approve_job, delete_job, toggle_user_active,
    bulk_toggle_users, set_job_status, toggle_job_featured, broadcast_job_telegram,
    admin_companies_verification, admin_verify_company, admin_reject_company, admin_rerun_ai_verification,
    admin_payments_dashboard, admin_update_payment_status
)
from jobsapp.views.employee import (
    ApplicantDashboardView, EditProfileView, EmployeeMyJobsListView, FavoriteListView,
    add_education, add_experience, add_skill, delete_education, delete_experience, delete_skill,
    mark_all_notifications_as_read, mark_notification_as_read, notifications_view, withdraw_application
)
from jobsapp.views.employer import (
    ApplicantPerJobView, ApplicantsListView, AppliedApplicantView, DashboardView,
    EmployerProfileEditView, JobCreateView, JobUpdateView, SendResponseView, delete_employer_job, filled,
    export_applicants_csv
)
from jobsapp.views.home import (
    AboutUsView, ApplyJobView, HomeView, JobDetailsView, JobListView, SearchView, SalaryCalculatorView, favorite
)

app_name = "jobs"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("favorite/", favorite, name="favorite"),
    path("search/", SearchView.as_view(), name="search"),
    path("salary-calculator/", SalaryCalculatorView.as_view(), name="salary-calculator"),

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

    # Public Job Pages
    path("apply-job/<int:job_id>/", ApplyJobView.as_view(), name="apply-job"),
    path("jobs/", JobListView.as_view(), name="jobs"),
    path("jobs/<int:id>/", JobDetailsView.as_view(), name="jobs-detail"),
    path("jobs/<slug:slug>/", JobDetailsView.as_view(), name="jobs-detail-slug"),
    path("about-us/", AboutUsView.as_view(), name="about-us"),
]
