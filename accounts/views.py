from django.contrib import auth, messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, FormView, RedirectView

from accounts.email_verification import send_verification_email
from accounts.forms import *
from accounts.models import User


class RegisterEmployeeView(CreateView):
    model = User
    form_class = EmployeeRegistrationForm
    template_name = "accounts/employee/register.html"
    success_url = "/"

    extra_context = {"title": "Register"}

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.success_url)
        return super().dispatch(self.request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get("password1")
            user.set_password(password)
            user.is_active = False  # inactive until email verified
            user.save()

            sent = send_verification_email(request, user)
            if sent:
                messages.success(
                    request,
                    f"✅ Account created! A verification link has been sent to <strong>{user.email}</strong>. "
                    "Please check your inbox (and spam folder) and click the link to activate your account."
                )
            else:
                messages.warning(
                    request,
                    "Account created but we could not send the verification email. "
                    "Please contact support."
                )
            return redirect("accounts:login")
        else:
            messages.error(request, "Please check the form and correct the highlighted errors.")
            return render(request, "accounts/employee/register.html", {"form": form})


class RegisterEmployerView(CreateView):
    model = User
    form_class = EmployerRegistrationForm
    template_name = "accounts/employer/register.html"
    success_url = "/"

    extra_context = {"title": "Register"}

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.success_url)
        return super().dispatch(self.request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get("password1")
            user.set_password(password)
            user.is_active = False  # inactive until email verified
            user.save()

            # Ensure Company record is created for this employer
            from accounts.models import Company
            company_name = form.cleaned_data.get("first_name", "Company")
            company_location = form.cleaned_data.get("last_name", "")
            Company.objects.get_or_create(user=user, defaults={"name": company_name, "location": company_location})

            sent = send_verification_email(request, user)
            if sent:
                messages.success(
                    request,
                    f"✅ Employer account created! A verification link has been sent to <strong>{user.email}</strong>. "
                    "Please check your inbox (and spam folder) and click the link to activate your account."
                )
            else:
                messages.warning(
                    request,
                    "Account created but we could not send the verification email. "
                    "Please contact support."
                )
            return redirect("accounts:login")
        else:
            messages.error(request, "Please check the form and correct the highlighted errors.")
            return render(request, "accounts/employer/register.html", {"form": form})


class VerifyEmailView(View):
    """
    Handles the email verification link: /verify-email/<token>/
    Activates the user account if the token is valid and not expired.
    """

    def get(self, request, token, *args, **kwargs):
        try:
            user = User.objects.get(email_token=token)
        except User.DoesNotExist:
            messages.error(request, "❌ This verification link is invalid or has already been used.")
            return redirect("accounts:login")

        if user.email_verified:
            messages.info(request, "✅ Your email is already verified. Please log in.")
            return redirect("accounts:login")

        if timezone.now() > user.email_token_expires:
            # Token expired — resend
            sent = send_verification_email(request, user)
            if sent:
                messages.warning(
                    request,
                    f"⏰ Your verification link expired. A new link has been sent to <strong>{user.email}</strong>."
                )
            else:
                messages.error(request, "Your verification link expired. Please register again.")
            return redirect("accounts:login")

        # Success — activate the account
        user.email_verified = True
        user.is_active = True
        user.save(update_fields=["email_verified", "is_active"])
        messages.success(
            request,
            "🎉 Your email has been verified! Your account is now active. Please log in."
        )
        return redirect("accounts:login")


class ResendVerificationView(View):
    """
    Resends the verification email from the login page link.
    """

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email", "").strip().lower()
        if not email:
            messages.error(request, "Please provide your email address.")
            return redirect("accounts:login")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal existence
            messages.success(
                request,
                f"If {email} is registered and unverified, a new verification link has been sent."
            )
            return redirect("accounts:login")

        if user.email_verified:
            messages.info(request, "Your email is already verified. Please log in.")
            return redirect("accounts:login")

        sent = send_verification_email(request, user)
        if sent:
            messages.success(
                request,
                f"A new verification link has been sent to <strong>{user.email}</strong>. "
                "Please check your inbox."
            )
        else:
            messages.error(request, "Could not send verification email. Please try again later.")
        return redirect("accounts:login")


class LoginView(FormView):
    """
    Provides the ability to login as a user with an email and password
    """

    success_url = "/"
    form_class = UserLoginForm
    template_name = "accounts/login.html"

    extra_context = {"title": "Login"}

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(self._redirect_for_user(self.request.user))
        return super().dispatch(self.request, *args, **kwargs)

    def _redirect_for_user(self, user):
        """Return the correct URL based on user role."""
        try:
            if "next" in self.request.GET and self.request.GET["next"]:
                return self.request.GET["next"]
            if user.is_superuser or user.is_staff:
                return "/analytics-dashboard/"
            if getattr(user, "role", None) == "employer":
                return "/en/employer/dashboard/"
            if getattr(user, "role", None) == "employee":
                return "/en/applicant/dashboard/"
        except Exception:
            pass
        return self.success_url

    def get_success_url(self):
        return self._redirect_for_user(self.request.user)

    def get_form_class(self):
        return self.form_class

    def form_valid(self, form):
        auth.login(self.request, form.get_user())
        return HttpResponseRedirect(self._redirect_for_user(form.get_user()))

    def form_invalid(self, form):
        """If the form is invalid, render the invalid form."""
        return self.render_to_response(self.get_context_data(form=form))


class LogoutView(RedirectView):
    """
    Provides users the ability to logout
    """

    pattern_name = "accounts:login"

    def get(self, request, *args, **kwargs):
        auth.logout(request)
        messages.success(request, "You are now logged out")
        return redirect("accounts:login")
