from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from accounts.forms import EmployeeProfileUpdateForm
from accounts.models import User
from jobsapp.decorators import user_is_employee
from jobsapp.forms import (
    ApplicantProfileForm, CandidateSkillForm, EducationForm, WorkExperienceForm
)
from jobsapp.models import (
    Applicant, ApplicantProfile, CandidateSkill, Education, Favorite, Job, Notification, WorkExperience
)
from jobsapp.utils.recommendation import calculate_job_match_score


@method_decorator(login_required(login_url=reverse_lazy("accounts:login")), name="dispatch")
@method_decorator(user_is_employee, name="dispatch")
class ApplicantDashboardView(TemplateView):
    template_name = "jobs/employee/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get or create profile
        profile, created = ApplicantProfile.objects.get_or_create(user=user)

        # Applications
        applications = Applicant.objects.select_related("job", "job__user").filter(user=user).order_by("-created_at")

        # Favorites
        favorites = Favorite.objects.select_related("job", "job__user").filter(user=user, soft_deleted=False)

        # Job Recommendations with match scores
        all_jobs = Job.objects.filter(filled=False, status="approved")[:10]
        recommended_jobs = []
        for job in all_jobs:
            score = calculate_job_match_score(user, job)
            recommended_jobs.append({"job": job, "match_score": score})

        # Sort recommendations by match score descending
        recommended_jobs.sort(key=lambda x: x["match_score"], reverse=True)

        context["profile"] = profile
        context["completion_percentage"] = profile.completion_percentage
        context["applications"] = applications
        context["total_applications"] = applications.count()
        context["pending_applications"] = applications.filter(status=1).count()
        context["shortlisted_applications"] = applications.filter(status=2).count()
        context["accepted_applications"] = applications.filter(status=4).count()
        context["favorites_count"] = favorites.count()
        context["recommended_jobs"] = recommended_jobs[:5]
        context["unread_notifications_count"] = Notification.objects.filter(user=user, is_read=False).count()
        return context


@method_decorator(login_required(login_url=reverse_lazy("accounts:login")), name="dispatch")
@method_decorator(user_is_employee, name="dispatch")
class EmployeeMyJobsListView(ListView):
    model = Applicant
    template_name = "jobs/employee/my-applications.html"
    context_object_name = "applicants"
    paginate_by = 6

    def get_queryset(self):
        self.queryset = (
            self.model.objects.select_related("job").filter(user_id=self.request.user.id).order_by("-created_at")
        )
        status_param = self.request.GET.get("status")
        if status_param and status_param.isdigit() and int(status_param) > 0:
            self.queryset = self.queryset.filter(status=int(status_param))
        return self.queryset


class EditProfileView(UpdateView):
    model = User
    form_class = EmployeeProfileUpdateForm
    context_object_name = "employee"
    template_name = "jobs/employee/edit-profile.html"
    success_url = reverse_lazy("accounts:employee-profile-update")

    @method_decorator(login_required(login_url=reverse_lazy("accounts:login")))
    @method_decorator(user_is_employee)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(self.request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile, _ = ApplicantProfile.objects.get_or_create(user=user)
        context["profile_form"] = ApplicantProfileForm(instance=profile)
        context["education_form"] = EducationForm()
        context["experience_form"] = WorkExperienceForm()
        context["skill_form"] = CandidateSkillForm()
        context["educations"] = user.educations.all()
        context["experiences"] = user.experiences.all()
        context["skills"] = user.skills.all()
        return context

    def post(self, request, *args, **kwargs):
        user = self.request.user
        profile, _ = ApplicantProfile.objects.get_or_create(user=user)
        user_form = EmployeeProfileUpdateForm(request.POST, request.FILES, instance=user)
        profile_form = ApplicantProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("jobs:applicant-dashboard")

        context = self.get_context_data()
        context["form"] = user_form
        context["profile_form"] = profile_form
        return self.render_to_response(context)


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employee
def add_education(request):
    if request.method == "POST":
        form = EducationForm(request.POST)
        if form.is_valid():
            edu = form.save(commit=False)
            edu.user = request.user
            edu.save()
            messages.success(request, "Education added successfully.")
        else:
            messages.error(request, "Error adding education. Please check your input.")
    return redirect("jobs:employee-profile-update")


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employee
def delete_education(request, pk):
    edu = get_object_or_404(Education, pk=pk, user=request.user)
    edu.delete()
    messages.success(request, "Education deleted successfully.")
    return redirect("jobs:employee-profile-update")


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employee
def add_experience(request):
    if request.method == "POST":
        form = WorkExperienceForm(request.POST)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.user = request.user
            exp.save()
            messages.success(request, "Experience added successfully.")
        else:
            messages.error(request, "Error adding experience.")
    return redirect("jobs:employee-profile-update")


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employee
def delete_experience(request, pk):
    exp = get_object_or_404(WorkExperience, pk=pk, user=request.user)
    exp.delete()
    messages.success(request, "Work experience deleted successfully.")
    return redirect("jobs:employee-profile-update")


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employee
def add_skill(request):
    if request.method == "POST":
        form = CandidateSkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.user = request.user
            skill.save()
            messages.success(request, "Skill added successfully.")
        else:
            messages.error(request, "Skill already exists or invalid.")
    return redirect("jobs:employee-profile-update")


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employee
def delete_skill(request, pk):
    skill = get_object_or_404(CandidateSkill, pk=pk, user=request.user)
    skill.delete()
    messages.success(request, "Skill deleted successfully.")
    return redirect("jobs:employee-profile-update")


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employee
def withdraw_application(request, applicant_id):
    applicant = get_object_or_404(Applicant, id=applicant_id, user=request.user)
    if applicant.status == 1:  # Only pending
        job_title = applicant.job.title
        applicant.delete()
        messages.success(request, f"Your application for '{job_title}' has been withdrawn.")
    else:
        messages.error(request, "You can only withdraw applications that are pending.")
    return redirect("jobs:employee-my-applications")


@method_decorator(login_required(login_url=reverse_lazy("accounts:login")), name="dispatch")
@method_decorator(user_is_employee, name="dispatch")
class FavoriteListView(ListView):
    model = Favorite
    template_name = "jobs/employee/favorites.html"
    context_object_name = "favorites"

    def get_queryset(self):
        return self.model.objects.select_related("job__user").filter(soft_deleted=False, user=self.request.user)


@login_required(login_url=reverse_lazy("accounts:login"))
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "jobs/notifications.html", {"notifications": notifications})


@login_required(login_url=reverse_lazy("accounts:login"))
def mark_notification_as_read(request, pk):
    notification = get_object_or_404(Notification, id=pk, user=request.user)
    notification.is_read = True
    notification.save()
    if notification.link:
        return redirect(notification.link)
    return redirect("jobs:notifications")


@login_required(login_url=reverse_lazy("accounts:login"))
def mark_all_notifications_as_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("jobs:notifications")
