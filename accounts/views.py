from django.contrib import auth, messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, FormView, RedirectView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

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
            user.first_name = form.cleaned_data.get("first_name", "").strip()
            user.last_name = form.cleaned_data.get("last_name", "").strip()
            user.gender = form.cleaned_data.get("gender")
            user.phone_number = form.cleaned_data.get("phone_number", "").strip()
            user.role = "employee"
            user.is_active = True
            user.save()
            messages.success(
                request,
                f"Employee account registered successfully for {user.first_name} {user.last_name}! Please log in with your Google email ({user.email})."
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
            user.first_name = form.cleaned_data.get("first_name", "").strip()
            user.last_name = form.cleaned_data.get("last_name", "").strip()
            user.gender = form.cleaned_data.get("gender")
            user.phone_number = form.cleaned_data.get("phone_number", "").strip()
            user.role = "employer"
            user.is_active = True
            user.save()

            # Ensure Company record is created for this employer
            from accounts.models import Company
            company_name = form.cleaned_data.get("company_name", "").strip() or f"{user.first_name}'s Company"
            Company.objects.update_or_create(user=user, defaults={"name": company_name})

            messages.success(
                request,
                f"Employer account for '{company_name}' registered successfully! Please log in with your Google email ({user.email})."
            )
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
                company = getattr(user, "company", None)
                if not company or not company.is_license_verified:
                    return "/en/employer/verify-license/"
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
    Directs verified employers to employer dashboard, unverified employers to verify-license,
    platform admins to analytics dashboard, and applicants to applicant dashboard.
    """
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        from django.urls import reverse
        user = self.request.user
        if not user.is_authenticated:
            return reverse("accounts:login")
        if user.is_superuser or user.is_staff:
            return reverse("jobs:admin-analytics-dashboard")
        if getattr(user, "role", None) == "employer":
            company = getattr(user, "company", None)
            if not company or not company.is_license_verified:
                return reverse("accounts:employer-verify-license")
            return reverse("jobs:employer-dashboard")
        return reverse("jobs:applicant-dashboard")


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

        # Run AI Verification Engine with Government Registry cross-check
        result = verify_ethiopian_business_license(
            uploaded_file,
            tin_input=tin_number,
            company_name=company.name
        )

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


@method_decorator(csrf_exempt, name="dispatch")
class GoogleOneTapLoginView(View):
    """
    Handles Google One Tap sign-in / signup.
    Receives signed Google ID Token (credential), verifies it with Google,
    and signs the user in instantly with their Google account.
    """
    def post(self, request, *args, **kwargs):
        import json
        import requests
        from django.contrib.auth import login as auth_login
        from accounts.models import User
        from django.utils import timezone
        from django.conf import settings
        from django.http import JsonResponse

        credential = request.POST.get("credential")
        if not credential:
            try:
                body_data = json.loads(request.body.decode("utf-8"))
                credential = body_data.get("credential")
            except Exception:
                pass

        if not credential:
            return JsonResponse({"status": "error", "message": "No credential token provided"}, status=400)

        # Verify Google ID token via Google TokenInfo API
        try:
            verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
            res = requests.get(verify_url, timeout=10)
            if res.status_code != 200:
                return JsonResponse({"status": "error", "message": "Invalid Google token"}, status=400)
            data = res.json()
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

        # Validate Audience if configured
        expected_client_id = getattr(settings, "SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "")
        token_aud = data.get("aud")
        if expected_client_id and token_aud and token_aud != expected_client_id:
            return JsonResponse({"status": "error", "message": "Google Client ID mismatch"}, status=400)

        email = data.get("email")
        if not email:
            return JsonResponse({"status": "error", "message": "No email returned by Google"}, status=400)

        email = email.lower().strip()
        first_name = data.get("given_name") or data.get("name", "")
        last_name = data.get("family_name") or ""

        admin_emails = ["wubantetilahun@gmail.com", "wubante19@gmail.com", "admin@admin.com"]
        is_admin = email in admin_emails

        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_user(
                email=email,
                role="employer" if is_admin else "employee",
                first_name=first_name,
                last_name=last_name,
                is_verified=True,
                email_verified_at=timezone.now(),
            )
            if is_admin:
                user.is_staff = True
                user.is_superuser = True
                user.save()
        else:
            updated = False
            if not user.first_name and first_name:
                user.first_name = first_name
                updated = True
            if not user.last_name and last_name:
                user.last_name = last_name
                updated = True
            if not user.is_verified:
                user.is_verified = True
                user.email_verified_at = timezone.now()
                updated = True
            if is_admin and (not user.is_staff or not user.is_superuser):
                user.is_staff = True
                user.is_superuser = True
                updated = True
            if updated:
                user.save()

        # Log the user in with default backend
        auth_login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        # Determine redirect route
        from django.urls import reverse
        if user.is_superuser or user.is_staff:
            redirect_url = reverse("jobs:admin-analytics-dashboard")
        elif getattr(user, "role", None) == "employer":
            company = getattr(user, "company", None)
            if not company or not company.is_license_verified:
                redirect_url = reverse("accounts:employer-verify-license")
            else:
                redirect_url = reverse("jobs:employer-dashboard")
        else:
            redirect_url = reverse("jobs:applicant-dashboard")

        return JsonResponse({
            "status": "success",
            "redirect_url": redirect_url,
            "user": {
                "email": user.email,
                "name": user.get_full_name() or user.email
            }
        })
