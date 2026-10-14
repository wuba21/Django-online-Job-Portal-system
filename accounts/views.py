from django.contrib import auth, messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, FormView, RedirectView

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
            user.is_active = True
            user.save()
            messages.success(request, "Account created successfully! Please log in with your email and password.")
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
            user.is_active = True
            user.save()
            # Ensure Company record is created for this employer
            from accounts.models import Company
            company_name = form.cleaned_data.get("first_name", "Company")
            company_location = form.cleaned_data.get("last_name", "")
            Company.objects.get_or_create(user=user, defaults={"name": company_name, "location": company_location})
            messages.success(request, "Employer account created successfully! Please log in with your email and password.")
            return redirect("accounts:login")
        else:
            messages.error(request, "Please check the form and correct the highlighted errors.")
            return render(request, "accounts/employer/register.html", {"form": form})


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


class LoginRedirectRouteView(RedirectView):
    """
    Intelligent post-login / OAuth redirect:
    Directs verified employers to /en/employer/dashboard/, unverified employers to /en/employer/verify-license/,
    and employees to /en/applicant/dashboard/
    """
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        if not user.is_authenticated:
            return "/en/login/"
        if user.is_superuser or user.is_staff:
            return "/analytics-dashboard/"
        if getattr(user, "role", None) == "employer":
            company = getattr(user, "company", None)
            if not company or not company.is_license_verified:
                return "/en/employer/verify-license/"
            return "/en/employer/dashboard/"
        return "/en/applicant/dashboard/"


class EmployerLicenseVerifyView(View):
    """
    AI-powered Ethiopian Business License Verification View.
    Allows employer to upload TIN & Trade License scan.
    Runs automated AI stamp & TIN validation.
    """
    template_name = "accounts/employer/verify_license.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if getattr(request.user, "role", None) != "employer" and not request.user.is_superuser:
            return redirect("jobs:home")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        from accounts.models import Company
        company, _ = Company.objects.get_or_create(
            user=request.user,
            defaults={"name": request.user.get_full_name() or "My Company"}
        )
        return render(request, self.template_name, {"company": company})

    def post(self, request, *args, **kwargs):
        from accounts.models import Company
        from accounts.license_validator import verify_ethiopian_business_license
        from django.utils import timezone

        company, _ = Company.objects.get_or_create(
            user=request.user,
            defaults={"name": request.user.get_full_name() or "My Company"}
        )

        company_name = request.POST.get("company_name", "").strip()
        tin_number = request.POST.get("tin_number", "").strip()
        uploaded_file = request.FILES.get("license_document")

        if company_name:
            company.name = company_name

        if not uploaded_file:
            messages.error(request, "እባክዎ ህጋዊ የንግድ ፈቃድዎን (PDF ወይም ፎቶ) ይስቀሉ።")
            return render(request, self.template_name, {"company": company})

        # Save the uploaded license document
        company.license_document = uploaded_file
        company.tin_number = tin_number

        # Run AI Verification Engine
        result = verify_ethiopian_business_license(uploaded_file, tin_input=tin_number)

        company.license_ai_confidence = result["confidence"]
        if result["tin_number"]:
            company.tin_number = result["tin_number"]

        if result["is_valid"]:
            company.license_status = "verified"
            company.license_verified_at = timezone.now()
            company.license_rejection_reason = ""
            company.save()

            reasons_summary = "፣ ".join(result["reasons"])
            messages.success(
                request,
                f"🎉 የንግድ ፈቃድዎ በ AI በስኬት ተረጋግጧል! (Confidence: {result['confidence']}%) — {reasons_summary}። አሁን ወደ አሰሪ ዳሽቦርድ ገብተው ስራ መለጠፍ ይችላሉ!"
            )
            return redirect("jobs:employer-dashboard")
        else:
            company.license_status = "rejected"
            company.license_rejection_reason = result["error_message"] or "የንግድ ፈቃድ ማህተም ወይም TIN አልተገኘም።"
            company.save()

            messages.error(
                request,
                f"❌ ማረጋገጫው አልተሳካም (Confidence: {result['confidence']}%)፦ {company.license_rejection_reason}። እባክዎ ኦርጅናል ማህተም እና TIN ቁጥር በግልጽ የሚታይበትን ፈቃድ እንደገና ይስቀሉ።"
            )
            return render(request, self.template_name, {"company": company, "result": result})
