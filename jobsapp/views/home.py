from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseNotAllowed, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from categories.models import Category
from jobsapp.decorators import user_is_employee
from jobsapp.forms import ApplyJobForm
from jobsapp.models import (
    Applicant, ApplicantProfile, ETHIOPIAN_LOCATIONS, EXPERIENCE_LEVEL_CHOICES,
    Favorite, Job, JobAlert, WORK_MODE_CHOICES, CandidateSkill, WorkExperience,
    EXPERIENCE_YEARS_CHOICES, NOTICE_PERIOD_CHOICES, EDUCATION_LEVEL_CHOICES
)
from jobsapp.utils.notifications import create_notification, send_event_email
from jobsapp.utils.recommendation import calculate_job_match_score, get_recommended_jobs_for_user, invalidate_recommendation_cache
from jobsapp.utils.ai_resume_detector import extract_text_from_file, analyze_resume_authenticity
from django.views.decorators.http import require_POST


class HomeView(ListView):
    model = Job
    template_name = "home.html"
    context_object_name = "jobs"

    def get_queryset(self):
        return self.model.objects.select_related("user", "company").prefetch_related("tags").filter(filled=False, status="approved")[:6]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Reuse already fetched jobs for trending to eliminate redundant DB query
        jobs_list = list(context["jobs"])
        context["trendings"] = jobs_list[:3]
        context["categories"] = Category.objects.only("id", "name")[:8]
        context["locations"] = ETHIOPIAN_LOCATIONS

        if self.request.user.is_authenticated and self.request.user.is_employee:
            context["recommended_jobs"] = get_recommended_jobs_for_user(self.request.user, limit=3)

        return context


class AboutUsView(TemplateView):
    template_name = "about_us.html"


class SalaryCalculatorView(TemplateView):
    template_name = "jobs/salary_calculator.html"


class SearchView(ListView):
    model = Job
    template_name = "jobs/search.html"
    context_object_name = "jobs"
    paginate_by = 6

    def get_queryset(self):
        queryset = self.model.objects.select_related("user", "company").prefetch_related("tags").filter(filled=False, status="approved")

        # Filters
        position = self.request.GET.get("position") or self.request.GET.get("q")
        location = self.request.GET.get("location")
        category = self.request.GET.get("category")
        work_mode = self.request.GET.get("work_mode")
        experience = self.request.GET.get("experience")
        min_salary = self.request.GET.get("min_salary")
        sort_by = self.request.GET.get("sort_by")

        if position:
            queryset = queryset.filter(
                Q(title__icontains=position) |
                Q(description__icontains=position) |
                Q(company_name__icontains=position)
            )
        if location and location != "All" and location != "Any":
            queryset = queryset.filter(location__icontains=location)
        if category and category != "All":
            queryset = queryset.filter(category__icontains=category)
        if work_mode and work_mode != "All":
            queryset = queryset.filter(work_mode=work_mode)
        if experience and experience != "All":
            queryset = queryset.filter(experience_level=experience)
        if min_salary and min_salary.isdigit():
            queryset = queryset.filter(salary__gte=int(min_salary))

        # Sorting
        if sort_by == "salary":
            queryset = queryset.order_by("-salary", "-id")
        elif sort_by == "oldest":
            queryset = queryset.order_by("created_at")
        else:
            queryset = queryset.order_by("-created_at")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["locations"] = ETHIOPIAN_LOCATIONS
        context["experience_levels"] = EXPERIENCE_LEVEL_CHOICES
        context["work_modes"] = WORK_MODE_CHOICES
        context["selected_position"] = self.request.GET.get("position", "")
        context["selected_location"] = self.request.GET.get("location", "")
        context["selected_category"] = self.request.GET.get("category", "")
        context["selected_work_mode"] = self.request.GET.get("work_mode", "")
        context["selected_experience"] = self.request.GET.get("experience", "")
        context["selected_sort"] = self.request.GET.get("sort_by", "recent")
        return context


class JobListView(ListView):
    model = Job
    template_name = "jobs/jobs.html"
    context_object_name = "jobs"
    paginate_by = 6

    def get_queryset(self):
        return self.model.objects.select_related("user", "company").prefetch_related("tags").filter(filled=False, status="approved").order_by("-created_at")

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["total_jobs"] = self.model.objects.filter(filled=False, status="approved").count()
        data["categories"] = Category.objects.all()
        data["locations"] = ETHIOPIAN_LOCATIONS
        return data


class JobDetailsView(DetailView):
    model = Job
    template_name = "jobs/details.html"
    context_object_name = "job"
    pk_url_kwarg = "id"

    def get_queryset(self):
        return self.model.objects.select_related("user", "company").prefetch_related("tags", "images")

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        # Try slug from URL kwargs (root-level or /jobs/<slug>/ URLs)
        slug = self.kwargs.get("slug")
        pk = self.kwargs.get("id")
        if slug:
            return get_object_or_404(queryset, slug=slug)
        if pk:
            return get_object_or_404(queryset, pk=pk)
        raise Http404("Job doesn't exist")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.object
        user = self.request.user

        context["already_applied"] = False
        context["is_favorited"] = False
        context["match_score"] = 0

        if user.is_authenticated:
            context["already_applied"] = Applicant.objects.filter(user=user, job=job).exists()
            context["is_favorited"] = Favorite.objects.filter(user=user, job=job, soft_deleted=False).exists()
            if user.is_employee:
                context["match_score"] = calculate_job_match_score(user, job)

                profile, _ = ApplicantProfile.objects.get_or_create(user=user)
                context["applicant_profile"] = profile

                has_cv = bool(
                    profile.cv_file
                    or (hasattr(user, "resume_cvs") and user.resume_cvs.exists())
                )
                has_phone = bool(user.phone_number and user.phone_number.strip())
                has_name = bool(user.first_name and user.first_name.strip() and user.last_name and user.last_name.strip())
                has_title = bool(profile.title and profile.title.strip())
                has_skills = bool(hasattr(user, "skills") and user.skills.exists())
                has_email = bool(user.email and user.email.strip())
                has_gender = bool(user.gender and user.gender.strip())
                has_location = bool(profile.location and profile.location.strip())
                has_experience = bool(hasattr(user, "experiences") and user.experiences.exists())

                missing_reqs = []
                if not has_name:
                    missing_reqs.append({
                        "id": "name",
                        "title": "Full Name",
                        "desc": "Please provide your first and last name so employers know who is applying.",
                        "fix_url": reverse("accounts:employee-profile-update"),
                        "fix_text": "Add Name"
                    })
                if not has_phone:
                    missing_reqs.append({
                        "id": "phone",
                        "title": "Contact Phone Number",
                        "desc": "Employers require a contact phone number to reach you for interview invitations.",
                        "fix_url": reverse("accounts:employee-profile-update"),
                        "fix_text": "Add Phone"
                    })
                if not has_email:
                    missing_reqs.append({
                        "id": "email",
                        "title": "Email Address",
                        "desc": "A valid email address is required for communication.",
                        "fix_url": reverse("accounts:employee-profile-update"),
                        "fix_text": "Add Email"
                    })
                if not has_gender:
                    missing_reqs.append({
                        "id": "gender",
                        "title": "Gender",
                        "desc": "Please specify your gender for equal opportunity compliance.",
                        "fix_url": reverse("accounts:employee-profile-update"),
                        "fix_text": "Set Gender"
                    })
                if not has_location:
                    missing_reqs.append({
                        "id": "location",
                        "title": "Address / City Location",
                        "desc": "Specify your city or location so employers can assess proximity.",
                        "fix_url": reverse("accounts:employee-profile-update"),
                        "fix_text": "Add Location"
                    })
                if not has_title:
                    missing_reqs.append({
                        "id": "title",
                        "title": "Professional Title / Profession",
                        "desc": "Specify your profession or career headline (e.g. Software Engineer, Accountant, Sales Manager).",
                        "fix_url": reverse("accounts:employee-profile-update"),
                        "fix_text": "Add Title"
                    })
                if not has_experience:
                    missing_reqs.append({
                        "id": "experience",
                        "title": "Work Experience",
                        "desc": "Add at least one work experience entry so employers can evaluate your background.",
                        "fix_url": reverse("accounts:employee-profile-update"),
                        "fix_text": "Add Experience"
                    })
                if not has_skills:
                    missing_reqs.append({
                        "id": "skills",
                        "title": "Key Skills",
                        "desc": "Add your primary skills so employers can verify your qualifications for the role.",
                        "fix_url": reverse("jobs:applicant-dashboard") + "#skillsSection",
                        "fix_text": "Add Skills"
                    })
                if not has_cv:
                    missing_reqs.append({
                        "id": "cv",
                        "title": "Resume / CV Document",
                        "desc": "Employers require a Resume/CV. You can attach one below or generate one with Auto CV Builder.",
                        "fix_url": reverse("resume_cv:auto_builder"),
                        "fix_text": "Build CV Online"
                    })

                context["has_cv"] = has_cv
                context["has_phone"] = has_phone
                context["has_name"] = has_name
                context["has_title"] = has_title
                context["has_skills"] = has_skills
                context["has_email"] = has_email
                context["has_gender"] = has_gender
                context["has_location"] = has_location
                context["has_experience"] = has_experience
                context["ethiopian_locations"] = ETHIOPIAN_LOCATIONS
                context["experience_years_choices"] = EXPERIENCE_YEARS_CHOICES
                context["notice_period_choices"] = NOTICE_PERIOD_CHOICES
                context["education_level_choices"] = EDUCATION_LEVEL_CHOICES
                context["missing_requirements"] = missing_reqs
                context["is_ready_to_apply"] = len(missing_reqs) == 0

        return context


class ApplyJobView(CreateView):
    model = Applicant
    form_class = ApplyJobForm
    slug_field = "job_id"
    slug_url_kwarg = "job_id"

    @method_decorator(login_required(login_url=reverse_lazy("accounts:login")))
    @method_decorator(user_is_employee)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(self.request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(self._allowed_methods())

    def post(self, request, *args, **kwargs):
        try:
            job_id = self.kwargs.get("job_id")
            job = get_object_or_404(Job, id=job_id)

            if job.filled or job.is_expired:
                messages.error(request, "This job is closed or has expired.")
                return HttpResponseRedirect(reverse_lazy("jobs:jobs-detail", kwargs={"id": job.id}))

            existing = Applicant.objects.filter(user=request.user, job=job).exists()
            if existing:
                messages.info(request, "You have already applied for this job.")
                return HttpResponseRedirect(reverse_lazy("jobs:jobs-detail", kwargs={"id": job.id}))

            # Validate Required Applicant Information
            user = request.user
            profile, _ = ApplicantProfile.objects.get_or_create(user=user)
            uploaded_cv = request.FILES.get("cv")

            # ── Process Inline Quick-Complete Fields from Modal ──
            user_changed = False
            profile_changed_fields = []

            # 1. Full Name
            inline_first = request.POST.get("first_name", "").strip()
            inline_last = request.POST.get("last_name", "").strip()
            if inline_first and not (user.first_name and user.first_name.strip()):
                user.first_name = inline_first
                user_changed = True
            if inline_last and not (user.last_name and user.last_name.strip()):
                user.last_name = inline_last
                user_changed = True

            # 2. Phone Number
            inline_phone = request.POST.get("phone_number", "").strip()
            if inline_phone and not (user.phone_number and user.phone_number.strip()):
                user.phone_number = inline_phone
                user_changed = True

            # 3. Gender
            inline_gender = request.POST.get("gender", "").strip()
            if inline_gender in ("male", "female") and not (user.gender and user.gender.strip()):
                user.gender = inline_gender
                user_changed = True

            # 4. Location / Address
            inline_location = request.POST.get("location", "").strip()
            if inline_location and not (profile.location and profile.location.strip()):
                profile.location = inline_location
                profile_changed_fields.append("location")

            # 5. Professional Title
            inline_title = request.POST.get("title", "").strip()
            if inline_title and not (profile.title and profile.title.strip()):
                profile.title = inline_title
                profile_changed_fields.append("title")

            # Save user changes
            if user_changed:
                user.save(update_fields=[f for f in ["first_name", "last_name", "phone_number", "gender"] if getattr(user, f)])

            # Save profile changes
            if profile_changed_fields:
                profile.save(update_fields=profile_changed_fields)

            # 6. Quick Skills (comma-separated)
            inline_skills = request.POST.get("quick_skills", "").strip()
            if inline_skills and not (hasattr(user, "skills") and user.skills.exists()):
                for skill_name in inline_skills.split(","):
                    skill_name = skill_name.strip()
                    if skill_name and len(skill_name) <= 100:
                        CandidateSkill.objects.get_or_create(
                            user=user, name=skill_name,
                            defaults={"level": "intermediate"}
                        )

            # 7. Quick Work Experience
            inline_exp_title = request.POST.get("exp_title", "").strip()
            inline_exp_company = request.POST.get("exp_company", "").strip()
            if inline_exp_title and inline_exp_company and not (hasattr(user, "experiences") and user.experiences.exists()):
                from datetime import date
                WorkExperience.objects.create(
                    user=user,
                    title=inline_exp_title,
                    company=inline_exp_company,
                    is_current=True,
                    start_date=date.today()
                )

            # ── AI Resume/CV Verification ──
            if uploaded_cv:
                try:
                    cv_text = extract_text_from_file(uploaded_cv, uploaded_cv.name)
                    uploaded_cv.seek(0)  # Reset for later save
                    cv_analysis = analyze_resume_authenticity(cv_text, uploaded_cv.name)
                    if not cv_analysis["is_valid"] and cv_analysis["score"] < 30:
                        messages.error(
                            request,
                            f"❌ AI Resume Verification Failed: {cv_analysis['message']} "
                            f"Please upload a genuine, complete Resume/CV document."
                        )
                        return HttpResponseRedirect(reverse_lazy("jobs:jobs-detail", kwargs={"id": job.id}))
                except Exception:
                    pass  # Allow submission if AI check encounters an error

            # ── Re-validate ALL 8 Required Items ──
            has_cv = bool(
                uploaded_cv
                or profile.cv_file
                or (hasattr(user, "resume_cvs") and user.resume_cvs.exists())
            )
            has_phone = bool(user.phone_number and user.phone_number.strip())
            has_name = bool(user.first_name and user.first_name.strip() and user.last_name and user.last_name.strip())
            has_email = bool(user.email and user.email.strip())
            has_gender = bool(user.gender and user.gender.strip())
            has_location = bool(profile.location and profile.location.strip())
            has_title = bool(profile.title and profile.title.strip())
            has_experience = bool(hasattr(user, "experiences") and user.experiences.exists())
            has_skills = bool(hasattr(user, "skills") and user.skills.exists())

            missing_fields = []
            if not has_name:
                missing_fields.append("Full Name (First and Last name)")
            if not has_phone:
                missing_fields.append("Phone Number")
            if not has_email:
                missing_fields.append("Email Address")
            if not has_gender:
                missing_fields.append("Gender")
            if not has_location:
                missing_fields.append("Address / City Location")
            if not has_title:
                missing_fields.append("Professional Title / Profession")
            if not has_experience:
                missing_fields.append("Work Experience (at least 1 entry)")
            if not has_skills:
                missing_fields.append("Key Skills (at least 1 skill)")
            if not has_cv:
                missing_fields.append("Resume / CV Document (Please attach your CV)")

            if missing_fields:
                items_str = ", ".join(missing_fields)
                messages.error(
                    request,
                    f"⚠️ Application Incomplete: To apply for '{job.title}', you must complete the following: {items_str}. Please fill in the missing fields and try again."
                )
                return HttpResponseRedirect(reverse_lazy("jobs:jobs-detail", kwargs={"id": job.id}))

            # Create application safely
            comment_text = request.POST.get("comment", "").strip()
            expected_salary = request.POST.get("expected_salary", "").strip()
            experience_years = request.POST.get("experience_years", "").strip()
            notice_period = request.POST.get("notice_period", "").strip()
            education_level = request.POST.get("education_level", "").strip()
            portfolio_link = request.POST.get("portfolio_link", "").strip()

            applicant, created = Applicant.objects.get_or_create(
                user=user,
                job=job,
                defaults={"comment": comment_text}
            )
            if not created and comment_text:
                applicant.comment = comment_text

            if expected_salary:
                applicant.expected_salary = expected_salary
                if not profile.expected_salary:
                    profile.expected_salary = expected_salary
                    profile_changed_fields.append("expected_salary")

            if experience_years:
                applicant.experience_years = experience_years
                if not profile.experience_years:
                    profile.experience_years = experience_years
                    profile_changed_fields.append("experience_years")

            if notice_period:
                applicant.notice_period = notice_period
                if not profile.notice_period:
                    profile.notice_period = notice_period
                    profile_changed_fields.append("notice_period")

            if education_level:
                applicant.education_level = education_level
                if not profile.education_level:
                    profile.education_level = education_level
                    profile_changed_fields.append("education_level")

            if portfolio_link:
                applicant.portfolio_link = portfolio_link
                if not profile.website:
                    profile.website = portfolio_link
                    profile_changed_fields.append("website")

            # Calculate AI Job Match Score at application time
            try:
                applicant.ai_match_score = calculate_job_match_score(user, job)
            except Exception:
                applicant.ai_match_score = 0

            if uploaded_cv:
                applicant.cv = uploaded_cv
                if not profile.cv_file:
                    profile.cv_file = uploaded_cv
                    profile_changed_fields.append("cv_file")
            elif not applicant.cv:
                # Auto-link candidate's existing uploaded profile CV
                if profile.cv_file:
                    applicant.cv = profile.cv_file

            applicant.save()

            if profile_changed_fields:
                profile.save(update_fields=list(set(profile_changed_fields)))

            invalidate_recommendation_cache(user.id)

            messages.success(request, f"🎉 Successfully applied for '{job.title}'!")

            # Trigger Candidate Notification safely
            try:
                create_notification(
                    user=request.user,
                    title=f"Application Submitted: {job.title}",
                    message=f"You successfully applied for {job.title} at {job.company_name}.",
                    link=reverse_lazy("jobs:employee-my-applications")
                )
            except Exception:
                pass

            # Trigger Employer Notification safely if job owner exists
            try:
                if getattr(job, "user", None):
                    create_notification(
                        user=job.user,
                        title=f"New Applicant for {job.title}",
                        message=f"{request.user.get_full_name() or request.user.email} applied for {job.title}.",
                        link=reverse_lazy("jobs:employer-dashboard-applicants", kwargs={"job_id": job.id})
                    )
                    if job.user.email:
                        send_event_email(
                            user_email=job.user.email,
                            subject=f"📩 New Applicant for '{job.title}' - {request.user.get_full_name() or request.user.email}",
                            message=f"Hello,\n\nA new candidate, {request.user.get_full_name() or request.user.email}, has just applied for your vacancy '{job.title}'.\n\nYou can review their CV, experience, qualifications, and respond directly through your employer dashboard.",
                            action_url=request.build_absolute_uri(reverse_lazy("jobs:employer-dashboard-applicants", kwargs={"job_id": job.id})),
                            action_text="View Applicant & Resume"
                        )
            except Exception:
                pass

            # Send Email Alerts to Candidate safely
            try:
                if request.user.email:
                    send_event_email(
                        user_email=request.user.email,
                        subject=f"🎉 Application Received - {job.title}",
                        message=f"Hello {request.user.get_full_name() or 'Candidate'},\n\nYour application for '{job.title}' at {job.company_name} has been received successfully.\n\nThe employer has been notified and will review your qualifications. You can track your progress and interview updates from your candidate dashboard.",
                        action_url=request.build_absolute_uri(reverse_lazy("jobs:employee-my-applications")),
                        action_text="Track My Applications"
                    )
            except Exception:
                pass

            return HttpResponseRedirect(reverse_lazy("jobs:jobs-detail", kwargs={"id": job.id}))
        except Exception as e:
            messages.error(request, f"Application notice: {str(e)}")
            return HttpResponseRedirect(reverse_lazy("jobs:jobs-detail", kwargs={"id": self.kwargs.get("job_id", 1)}))


def favorite(request):
    if not request.user.is_authenticated:
        return JsonResponse(data={"auth": False, "status": "error", "message": "Login required"})

    job_id = request.POST.get("job_id")
    user_id = request.user.id
    try:
        fav = Favorite.objects.get(job_id=job_id, user_id=user_id, soft_deleted=False)
        fav.soft_deleted = True
        fav.save()
        return JsonResponse(
            data={"auth": True, "status": "removed", "message": "Job removed from your saved list"}
        )
    except Favorite.DoesNotExist:
        Favorite.objects.create(job_id=job_id, user_id=user_id, soft_deleted=False)
        return JsonResponse(data={"auth": True, "status": "added", "message": "Job saved successfully"})


def create_job_alert(request):
    """
    Subscribes a job seeker or guest email to instant alerts for a category or location.
    """
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        category = request.POST.get("category", "").strip()
        location = request.POST.get("location", "").strip()
        keywords = request.POST.get("keywords", "").strip()

        if not email and request.user.is_authenticated:
            email = request.user.email

        if not email:
            messages.error(request, "Please provide a valid email address to receive job alerts.")
            return redirect(request.META.get("HTTP_REFERER", "/"))

        user = request.user if request.user.is_authenticated else None
        alert, created = JobAlert.objects.get_or_create(
            email=email,
            category=category or "All",
            location=location or "All",
            defaults={"user": user, "keywords": keywords, "is_active": True}
        )

        messages.success(request, f"🎉 Job alert activated for {email}! You will receive notifications when matching vacancies are published.")

        try:
            send_event_email(
                user_email=email,
                subject="🔔 Job Alert Activated - Ethiopian Job Portal",
                message=f"Hello!\n\nYou have successfully subscribed to job alerts for:\n• Category: {category or 'All Categories'}\n• Location: {location or 'All Locations'}\n\nWe will notify you as soon as new matching vacancies are published by verified employers.",
                action_url=request.build_absolute_uri("/"),
                action_text="Explore Latest Vacancies"
            )
        except Exception:
            pass

    return redirect(request.META.get("HTTP_REFERER", "/"))


def send_job_alert_notifications(job, request=None):
    """
    Finds matching JobAlert subscribers and notifies them of a newly published job.
    """
    try:
        matching_alerts = JobAlert.objects.filter(is_active=True).filter(
            Q(category__iexact=job.category) | Q(category="All") | Q(category="") |
            Q(location__icontains=job.location) | Q(location="All") | Q(location="")
        ).distinct()

        base_url = request.build_absolute_uri(job.get_absolute_url()) if request else f"/jobs/{job.id}/"

        for alert in matching_alerts[:25]:
            send_event_email(
                user_email=alert.email,
                subject=f"🔔 New Vacancy Alert: {job.title} at {job.company_name}",
                message=f"Hello,\n\nA new vacancy matching your job alert criteria has just been published:\n\n• Job: {job.title}\n• Employer: {job.company_name}\n• Location: {job.location}\n• Mode: {job.get_work_mode_display()}\n\nClick below to view the requirements and apply before the deadline.",
                action_url=base_url,
                action_text="View Job & Apply"
            )
    except Exception:
        pass


@login_required(login_url=reverse_lazy("accounts:login"))
@require_POST
def verify_resume_api(request):
    """AJAX endpoint for instant AI Resume/CV authenticity verification."""
    uploaded = request.FILES.get("cv")
    if not uploaded:
        return JsonResponse({"is_valid": False, "score": 0, "message": "No file uploaded."})

    try:
        text = extract_text_from_file(uploaded, uploaded.name)
        uploaded.seek(0)
        analysis = analyze_resume_authenticity(text, uploaded.name)
        return JsonResponse({
            "is_valid": analysis["is_valid"],
            "score": analysis["score"],
            "message": analysis["message"],
            "status": analysis["status"],
            "detected_sections": analysis["detected_sections"],
            "extracted_skills": analysis["extracted_skills"],
            "word_count": analysis["word_count"],
        })
    except Exception as e:
        return JsonResponse({"is_valid": False, "score": 0, "message": f"Error analyzing file: {str(e)}"})
