from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseNotAllowed, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from categories.models import Category
from jobsapp.decorators import user_is_employee
from jobsapp.forms import ApplyJobForm
from jobsapp.models import Applicant, ETHIOPIAN_LOCATIONS, EXPERIENCE_LEVEL_CHOICES, Favorite, Job, WORK_MODE_CHOICES
from jobsapp.utils.notifications import create_notification, send_event_email
from jobsapp.utils.recommendation import calculate_job_match_score


class HomeView(ListView):
    model = Job
    template_name = "home.html"
    context_object_name = "jobs"

    def get_queryset(self):
        return self.model.objects.select_related("user", "company").prefetch_related("tags").filter(filled=False, status="approved")[:6]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trendings"] = self.model.objects.select_related("user", "company").prefetch_related("tags").filter(filled=False, status="approved")[:3]
        context["categories"] = Category.objects.all()[:8]
        context["locations"] = ETHIOPIAN_LOCATIONS

        if self.request.user.is_authenticated and self.request.user.is_employee:
            user_skills = set(self.request.user.skills.values_list("name", flat=True)) if hasattr(self.request.user, "skills") else set()
            user_title = getattr(getattr(self.request.user, "applicant_profile", None), "title", "") or ""
            user_location = getattr(getattr(self.request.user, "applicant_profile", None), "location", "") or ""
            
            all_jobs = self.model.objects.select_related("user", "company").prefetch_related("tags").filter(filled=False, status="approved")[:10]
            recommended = []
            for j in all_jobs:
                score = calculate_job_match_score(self.request.user, j, user_skills=user_skills, user_title=user_title, user_location=user_location)
                recommended.append({"job": j, "match_score": score})
            recommended.sort(key=lambda x: x["match_score"], reverse=True)
            context["recommended_jobs"] = recommended[:3]

        return context


class AboutUsView(TemplateView):
    template_name = "about_us.html"


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

    def get_object(self, queryset=None):
        # Try slug from URL kwargs (root-level or /jobs/<slug>/ URLs)
        slug = self.kwargs.get("slug")
        pk = self.kwargs.get("id")
        if slug:
            return get_object_or_404(Job, slug=slug)
        if pk:
            return get_object_or_404(Job, pk=pk)
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

            # Create application safely
            applicant, created = Applicant.objects.get_or_create(
                user=request.user,
                job=job,
                defaults={"comment": request.POST.get("comment", "")}
            )
            if "cv" in request.FILES:
                applicant.cv = request.FILES["cv"]
                applicant.save()

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
            except Exception:
                pass

            # Send Email Alerts safely
            try:
                if request.user.email:
                    send_event_email(
                        user_email=request.user.email,
                        subject=f"Application Confirmation - {job.title}",
                        message=f"Hello {request.user.get_full_name() or 'Candidate'},\n\nYour application for '{job.title}' at {job.company_name} has been received. You can track your status in your dashboard."
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
