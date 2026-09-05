from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from jobsapp.views import EditProfileView, EmployerProfileEditView
from .views import *

app_name = "accounts"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", LoginView.as_view(), name="accounts-login-alias"),
    path("accounts/logout/", LogoutView.as_view(), name="accounts-logout-alias"),
    path("employee/register/", RegisterEmployeeView.as_view(), name="employee-register"),
    path("employer/register/", RegisterEmployerView.as_view(), name="employer-register"),
    path("accounts/employee/register/", RegisterEmployeeView.as_view(), name="accounts-employee-register-alias"),
    path("accounts/employer/register/", RegisterEmployerView.as_view(), name="accounts-employer-register-alias"),
    path("employee/profile/update/", EditProfileView.as_view(), name="employee-profile-update"),
    path("employer/profile/update/", EmployerProfileEditView.as_view(), name="employer-profile-update"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
