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
    Favorite, Job, JobAlert, WORK_MODE_CHOICES
)
from jobsapp.utils.notifications import create_notification, send_event_email
from jobsapp.utils.recommendation import calculate_job_match_score, get_recommended_jobs_for_user, invalidate_recommendation_cache


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
                if not has_title:
                    missing_reqs.append({
                        "id": "title",
                        "title": "Professional Title / Profession",
                        "desc": "Specify your profession or career headline (e.g. Software Engineer, Accountant, Sales Manager).",
                        "fix_url": reverse("accounts:employee-profile-update"),
                        "fix_text": "Add Title"
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
            has_cv = bool(
                uploaded_cv
                or profile.cv_file
                or (hasattr(user, "resume_cvs") and user.resume_cvs.exists())
            )
            has_phone = bool(user.phone_number and user.phone_number.strip())
            has_name = bool(user.first_name and user.first_name.strip() and user.last_name and user.last_name.strip())
            has_title = bool(profile.title and profile.title.strip())
            has_skills = bool(hasattr(user, "skills") and user.skills.exists())

            missing_fields = []
            if not has_name:
                missing_fields.append("Full Name (First and Last name)")
            if not has_phone:
                missing_fields.append("Phone Number")
            if not has_title:
                missing_fields.append("Professional Title / Profession")
            if not has_skills:
                missing_fields.append("Key Skills (at least 1 skill)")
            if not has_cv:
                missing_fields.append("Resume / CV Document (Please attach your CV)")

            if missing_fields:
                items_str = ", ".join(missing_fields)
                messages.error(
                    request,
                    f"⚠️ Application Incomplete: To apply for '{job.title}', you must fulfill the required information first: {items_str}. Please complete this information in your profile or upload your CV."
                )
                return HttpResponseRedirect(reverse_lazy("jobs:jobs-detail", kwargs={"id": job.id}))

            # Create application safely
            comment_text = request.POST.get("comment", "").strip()
            applicant, created = Applicant.objects.get_or_create(
                user=user,
                job=job,
                defaults={"comment": comment_text}
            )
            if not created and comment_text:
                applicant.comment = comment_text

            if uploaded_cv:
                applicant.cv = uploaded_cv
                if not profile.cv_file:
                    profile.cv_file = uploaded_cv
                    profile.save(update_fields=["cv_file"])
            elif not applicant.cv:
                # Auto-link candidate's existing uploaded profile CV
                if profile.cv_file:
                    applicant.cv = profile.cv_file

            applicant.save()
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

