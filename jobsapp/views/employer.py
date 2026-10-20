from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.forms import EmployerProfileUpdateForm
from accounts.models import Company
from categories.models import Category
from django.db.models import Q
from jobsapp.decorators import user_is_employer
from jobsapp.forms import CompanyForm, CreateJobForm
from jobsapp.models import Applicant, Job, JobImage
from jobsapp.utils.notifications import create_notification, send_event_email
from jobsapp.utils.recommendation import calculate_job_match_score
from tags.models import Tag


class DashboardView(ListView):
    model = Job
    template_name = "jobs/employer/dashboard.html"
    context_object_name = "jobs"

    @method_decorator(login_required(login_url=reverse_lazy("accounts:login")))
    @method_decorator(user_is_employer)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(self.request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.filter(user_id=self.request.user.id).prefetch_related("tags")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_jobs = self.get_queryset()
        user_applicants = Applicant.objects.filter(job__user=self.request.user)

        context["total_jobs"] = user_jobs.count()
        context["active_jobs"] = user_jobs.filter(filled=False, last_date__gte=timezone.now()).count()
        context["expired_jobs"] = user_jobs.filter(last_date__lt=timezone.now()).count()
        context["total_applications"] = user_applicants.count()
        context["pending_applications"] = user_applicants.filter(status=1).count()
        context["shortlisted_applications"] = user_applicants.filter(status=2).count()
        context["accepted_applications"] = user_applicants.filter(status=4).count()

        company, _ = Company.objects.get_or_create(
            user=self.request.user,
            defaults={"name": self.request.user.get_full_name() or "Company"}
        )
        context["company"] = company
        return context


class ApplicantPerJobView(ListView):
    model = Applicant
    template_name = "jobs/employer/applicants.html"
    context_object_name = "applicants"
    paginate_by = 12

    @method_decorator(login_required(login_url=reverse_lazy("accounts:login")))
    @method_decorator(user_is_employer)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(self.request, *args, **kwargs)

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            self.job = get_object_or_404(Job, id=self.kwargs["job_id"])
        else:
            self.job = get_object_or_404(Job, id=self.kwargs["job_id"], user=self.request.user)

        queryset = Applicant.objects.select_related(
            "job", "user", "user__applicant_profile"
        ).prefetch_related(
            "user__skills", "user__educations", "user__experiences", "user__resume_cvs"
        ).filter(job=self.job)

        status_param = self.request.GET.get("status")
        if status_param and status_param.isdigit():
            queryset = queryset.filter(status=int(status_param))

        q = self.request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(user__email__icontains=q) |
                Q(user__applicant_profile__title__icontains=q)
            )

        applicants_list = list(queryset)
        for app in applicants_list:
            app.match_score = calculate_job_match_score(app.user, self.job)

        sort_param = self.request.GET.get("sort", "recent")
        if sort_param == "match":
            applicants_list.sort(key=lambda a: a.match_score, reverse=True)
        elif sort_param == "name":
            applicants_list.sort(key=lambda a: (a.user.get_full_name() or a.user.email).lower())
        else:
            applicants_list.sort(key=lambda a: a.id, reverse=True)

        return applicants_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = getattr(self, "job", None) or get_object_or_404(Job, id=self.kwargs["job_id"])
        context["job"] = job

        all_apps = Applicant.objects.filter(job=job)
        context["total_count"] = all_apps.count()
        context["pending_count"] = all_apps.filter(status=1).count()
        context["shortlisted_count"] = all_apps.filter(status=2).count()
        context["interview_count"] = all_apps.filter(status=3).count()
        context["accepted_count"] = all_apps.filter(status=4).count()
        context["rejected_count"] = all_apps.filter(status=5).count()
        context["current_status"] = self.request.GET.get("status", "all")
        context["current_sort"] = self.request.GET.get("sort", "recent")
        context["query"] = self.request.GET.get("q", "")
        return context


class JobCreateView(CreateView):
    template_name = "jobs/create.html"
    form_class = CreateJobForm
    extra_context = {"title": "Post New Job"}
    success_url = reverse_lazy("jobs:employer-dashboard")

    @method_decorator(login_required(login_url=reverse_lazy("accounts:login")))
    @method_decorator(user_is_employer)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(self.request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tags"] = Tag.objects.all()
        context["categories"] = Category.objects.all()
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        company, _ = Company.objects.get_or_create(
            user=self.request.user,
            defaults={"name": form.cleaned_data.get("company_name", "Company")}
        )
        form.instance.company = company

        response = super(JobCreateView, self).form_valid(form)
        job = self.object

        # Handle multiple screenshot / flyer photo uploads
        images = self.request.FILES.getlist("job_images")
        for img in images:
            JobImage.objects.create(job=job, image=img)

        # If logo was not uploaded separately, adopt the first screenshot as job logo
        if not job.logo and images:
            job.logo = images[0]
            job.save(update_fields=["logo"])

        if job.status == "approved":
            try:
                from jobsapp.views.home import send_job_alert_notifications
                send_job_alert_notifications(job, request=self.request)
            except Exception:
                pass

        messages.success(self.request, "Job posted successfully.")
        return response

    def get_success_url(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return reverse_lazy("jobs:admin-dashboard")
        return reverse_lazy("jobs:employer-dashboard")


@method_decorator(login_required(login_url=reverse_lazy("accounts:login")), name="dispatch")
@method_decorator(user_is_employer, name="dispatch")
class JobUpdateView(UpdateView):
    template_name = "jobs/update.html"
    form_class = CreateJobForm
    extra_context = {"title": "Edit Job"}
    slug_field = "id"
    slug_url_kwarg = "id"
    context_object_name = "job"

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Job.objects.all()
        return Job.objects.filter(user_id=self.request.user.id)

    def get_success_url(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return reverse_lazy("jobs:admin-dashboard")
        return reverse_lazy("jobs:employer-dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tags"] = Tag.objects.all()
        context["categories"] = Category.objects.all()
        context["existing_images"] = self.object.images.all() if self.object else []
        return context

    def form_valid(self, form):
        if not (self.request.user.is_superuser or self.request.user.is_staff):
            form.instance.user = self.request.user
        elif not form.instance.user_id:
            form.instance.user = self.request.user

        if not form.instance.company:
            company_name = form.cleaned_data.get("company_name", "Company")
            company, _ = Company.objects.get_or_create(
                name=company_name,
                defaults={"user": form.instance.user}
            )
            form.instance.company = company

        response = super(JobUpdateView, self).form_valid(form)
        job = self.object

        # Handle deleted existing images
        delete_ids = self.request.POST.getlist("delete_job_images")
        if delete_ids:
            JobImage.objects.filter(job=job, id__in=delete_ids).delete()

        # Handle new multiple screenshots / photos
        new_images = self.request.FILES.getlist("job_images")
        for img in new_images:
            JobImage.objects.create(job=job, image=img)

        if not job.logo and job.images.exists():
            first_img = job.images.first()
            if first_img:
                job.logo = first_img.image
                job.save(update_fields=["logo"])

        messages.success(self.request, "Job updated successfully.")
        return response


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employer
def delete_employer_job(request, job_id):
    if request.user.is_superuser or request.user.is_staff:
        job = get_object_or_404(Job, id=job_id)
    else:
        job = get_object_or_404(Job, id=job_id, user=request.user)
    title = job.title
    job.delete()
    messages.success(request, f"Job '{title}' deleted successfully.")
    referer = request.META.get("HTTP_REFERER")
    if referer and "jobs/" not in referer:
        return redirect(referer)
    if request.user.is_superuser or request.user.is_staff:
        return redirect("jobs:admin-dashboard")
    return redirect("jobs:employer-dashboard")


class ApplicantsListView(ListView):
    model = Applicant
    template_name = "jobs/employer/all-applicants.html"
    context_object_name = "applicants"
    paginate_by = 12

    @method_decorator(login_required(login_url=reverse_lazy("accounts:login")))
    @method_decorator(user_is_employer)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(self.request, *args, **kwargs)

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            qs = self.model.objects.select_related(
                "job", "user", "user__applicant_profile"
            ).prefetch_related(
                "user__skills", "user__educations", "user__experiences", "user__resume_cvs"
            )
        else:
            qs = self.model.objects.select_related(
                "job", "user", "user__applicant_profile"
            ).prefetch_related(
                "user__skills", "user__educations", "user__experiences", "user__resume_cvs"
            ).filter(job__user=self.request.user)

        status_param = self.request.GET.get("status")
        if status_param and status_param.isdigit():
            qs = qs.filter(status=int(status_param))

        job_param = self.request.GET.get("job_id")
        if job_param and job_param.isdigit():
            qs = qs.filter(job_id=int(job_param))

        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(user__email__icontains=q) |
                Q(job__title__icontains=q)
            )

        applicants_list = list(qs)
        for app in applicants_list:
            app.match_score = calculate_job_match_score(app.user, app.job)

        sort_param = self.request.GET.get("sort", "recent")
        if sort_param == "match":
            applicants_list.sort(key=lambda a: a.match_score, reverse=True)
        elif sort_param == "name":
            applicants_list.sort(key=lambda a: (a.user.get_full_name() or a.user.email).lower())
        else:
            applicants_list.sort(key=lambda a: a.id, reverse=True)

        return applicants_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_superuser or self.request.user.is_staff:
            base_qs = Applicant.objects.all()
            jobs_list = Job.objects.filter(filled=False).order_by("-created_at")
        else:
            base_qs = Applicant.objects.filter(job__user=self.request.user)
            jobs_list = Job.objects.filter(user=self.request.user, filled=False).order_by("-created_at")

        context["employer_jobs"] = jobs_list
        context["total_count"] = base_qs.count()
        context["pending_count"] = base_qs.filter(status=1).count()
        context["shortlisted_count"] = base_qs.filter(status=2).count()
        context["interview_count"] = base_qs.filter(status=3).count()
        context["accepted_count"] = base_qs.filter(status=4).count()
        context["rejected_count"] = base_qs.filter(status=5).count()
        context["current_status"] = self.request.GET.get("status", "all")
        context["current_job_id"] = self.request.GET.get("job_id", "")
        context["current_sort"] = self.request.GET.get("sort", "recent")
        context["query"] = self.request.GET.get("q", "")
        return context


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employer
def filled(request, job_id=None):
    job = get_object_or_404(Job, user_id=request.user.id, id=job_id)
    job.filled = not job.filled
    job.save()
    status_text = "marked as filled" if job.filled else "reopened"
    messages.success(request, f"Job '{job.title}' {status_text}.")
    return HttpResponseRedirect(reverse_lazy("jobs:employer-dashboard"))


@method_decorator(login_required(login_url=reverse_lazy("accounts:login")), name="dispatch")
@method_decorator(user_is_employer, name="dispatch")
class AppliedApplicantView(DetailView):
    model = Applicant
    template_name = "jobs/employer/applied-applicant-view.html"
    context_object_name = "applicant"
    slug_field = "id"
    slug_url_kwarg = "applicant_id"

    def get_queryset(self):
        qs = Applicant.objects.select_related("job", "user", "user__applicant_profile").prefetch_related(
            "user__skills", "user__experiences", "user__educations"
        )
        if self.request.user.is_superuser or self.request.user.is_staff:
            return qs.all()
        return qs.filter(job__user=self.request.user)


@method_decorator(login_required(login_url=reverse_lazy("accounts:login")), name="dispatch")
@method_decorator(user_is_employer, name="dispatch")
class SendResponseView(UpdateView):
    model = Applicant
    http_method_names = ["post"]
    pk_url_kwarg = "applicant_id"
    fields = ("status", "comment")

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Applicant.objects.all()
        return Applicant.objects.filter(job__user=self.request.user)

    def get_success_url(self):
        return reverse_lazy(
            "jobs:applied-applicant-view",
            kwargs={"job_id": self.object.job.id, "applicant_id": self.object.id},
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        new_status = int(request.POST.get("status", 1))
        old_status = self.object.status

        self.object.status = new_status
        self.object.comment = request.POST.get("comment", "")
        self.object.save()

        status_labels = {
            1: "Pending",
            2: "Shortlisted",
            3: "Interview Stage",
            4: "Accepted",
            5: "Rejected",
        }
        status_name = status_labels.get(new_status, "Updated")

        messages.success(self.request, f"Applicant status updated to '{status_name}'.")

        # Notify Candidate
        comment_note = f" Note: {self.object.comment}" if self.object.comment else ""
        create_notification(
            user=self.object.user,
            title=f"Application Update: {self.object.job.title} ({status_name})",
            message=f"Your application status for '{self.object.job.title}' at {self.object.job.company_name} was updated to '{status_name}'.{comment_note}",
            link=reverse_lazy("jobs:employee-my-applications")
        )

        send_event_email(
            user_email=self.object.user.email,
            subject=f"📋 Job Application Update - {self.object.job.title} ({status_name})",
            message=f"Hello {self.object.user.get_full_name() or 'Candidate'},\n\nYour application for the position '{self.object.job.title}' at {self.object.job.company_name} has been updated to: {status_name}.\n\nEmployer's Comment / Feedback:\n{self.object.comment or 'No specific comment provided.'}\n\nYou can log in to your dashboard to review next steps or interview arrangements.",
            action_url=request.build_absolute_uri(reverse_lazy("jobs:employee-my-applications")),
            action_text="View Application & Feedback"
        )

        return HttpResponseRedirect(self.get_success_url())


class EmployerProfileEditView(UpdateView):
    form_class = EmployerProfileUpdateForm
    context_object_name = "employer"
    template_name = "jobs/employer/edit-profile.html"
    success_url = reverse_lazy("accounts:employer-profile-update")

    @method_decorator(login_required(login_url=reverse_lazy("accounts:login")))
    @method_decorator(user_is_employer)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(self.request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company, _ = Company.objects.get_or_create(
            user=self.request.user,
            defaults={"name": self.request.user.get_full_name() or "Company"}
        )
        context["company_form"] = CompanyForm(instance=company)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user_form = EmployerProfileUpdateForm(request.POST, request.FILES, instance=self.object)
        company, _ = Company.objects.get_or_create(
            user=self.request.user,
            defaults={"name": self.request.user.get_full_name() or "Company"}
        )
        company_form = CompanyForm(request.POST, request.FILES, instance=company)

        if user_form.is_valid() and company_form.is_valid():
            user_form.save()
            company_form.save()
            messages.success(request, "Company and profile updated successfully.")
            return redirect("accounts:employer-profile-update")
        else:
            messages.error(request, "Please correct the highlighted errors below.")

        context = self.get_context_data()
        context["form"] = user_form
        context["company_form"] = company_form
        return self.render_to_response(context)


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employer
def export_applicants_csv(request, job_id):
    """
    Exports all applicants for a specific job into a clean CSV spreadsheet.
    """
    import csv
    from django.http import HttpResponse

    job = get_object_or_404(Job, id=job_id, user=request.user)
    applicants = Applicant.objects.select_related("user").filter(job=job)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="Applicants_{job.id}_{job.title.replace(" ", "_")}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Applicant Name", "Email", "Phone Number", "Applied Date", "Status", "Comment"])

    for app in applicants:
        writer.writerow([
            app.user.get_full_name() or app.user.email,
            app.user.email,
            getattr(app.user, "phone_number", "") or "N/A",
            app.created_at.strftime("%Y-%m-%d %H:%M"),
            app.get_status,
            app.comment or ""
        ])

    return response


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employer
def schedule_interview(request, applicant_id):
    """
    Schedules an interview date, time, and venue/meeting link for an applicant.
    Notifies the candidate via email and in-app alert.
    """
    if request.method == "POST":
        if request.user.is_superuser or request.user.is_staff:
            applicant = get_object_or_404(Applicant, id=applicant_id)
        else:
            applicant = get_object_or_404(Applicant, id=applicant_id, job__user=request.user)

        interview_date_str = request.POST.get("interview_date")
        interview_location = request.POST.get("interview_location", "").strip()
        interview_notes = request.POST.get("interview_notes", "").strip()

        applicant.status = 3  # Interview Stage
        if interview_date_str:
            try:
                applicant.interview_date = interview_date_str
            except Exception:
                pass
        applicant.interview_location = interview_location
        applicant.interview_notes = interview_notes
        applicant.save()

        date_display = applicant.interview_date.strftime("%B %d, %Y at %I:%M %p") if applicant.interview_date else "To be announced"
        messages.success(request, f"🎉 Interview successfully scheduled with {applicant.user.get_full_name() or applicant.user.email}!")

        # Send Notifications safely
        try:
            create_notification(
                user=applicant.user,
                title=f"📅 Interview Invitation: {applicant.job.title}",
                message=f"You have been invited to an interview for '{applicant.job.title}' by {applicant.job.company_name}. Scheduled: {date_display}. Mode/Location: {interview_location}.",
                link=reverse_lazy("jobs:employee-my-applications")
            )
            if applicant.user.email:
                send_event_email(
                    user_email=applicant.user.email,
                    subject=f"📅 Interview Scheduled - '{applicant.job.title}' at {applicant.job.company_name}",
                    message=f"Congratulations {applicant.user.get_full_name() or 'Candidate'}!\n\nYou have been selected for an interview for the vacancy '{applicant.job.title}' at {applicant.job.company_name}.\n\n📅 Interview Schedule Details:\n• Date & Time: {date_display}\n• Venue / Meeting Link: {interview_location or 'Online / Office'}\n• Additional Notes: {interview_notes or 'Please be ready and on time.'}\n\nPlease check your candidate dashboard for further updates.",
                    action_url=request.build_absolute_uri(reverse_lazy("jobs:employee-my-applications")),
                    action_text="View Interview Details"
                )
        except Exception:
            pass

    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("jobs:applied-applicant-view", job_id=applicant.job.id, applicant_id=applicant.id)


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employer
def quick_update_applicant_status(request, applicant_id, status_id):
    """
    1-Click recruitment status changer (Shortlist, Accept, Reject).
    """
    if request.user.is_superuser or request.user.is_staff:
        applicant = get_object_or_404(Applicant, id=applicant_id)
    else:
        applicant = get_object_or_404(Applicant, id=applicant_id, job__user=request.user)

    status_id = int(status_id)
    if status_id in [1, 2, 3, 4, 5]:
        applicant.status = status_id
        applicant.save()

        status_names = {
            1: "Pending",
            2: "Shortlisted",
            3: "Interview Stage",
            4: "Accepted",
            5: "Rejected",
        }
        status_name = status_names.get(status_id, "Updated")
        messages.success(request, f"Status for '{applicant.user.get_full_name() or applicant.user.email}' updated to {status_name}.")

        try:
            create_notification(
                user=applicant.user,
                title=f"Application Update: {applicant.job.title}",
                message=f"Your application status for '{applicant.job.title}' was updated to '{status_name}'.",
                link=reverse_lazy("jobs:employee-my-applications")
            )
            if applicant.user.email:
                send_event_email(
                    user_email=applicant.user.email,
                    subject=f"Application Update: {applicant.job.title} ({status_name})",
                    message=f"Hello {applicant.user.get_full_name() or 'Candidate'},\n\nYour application for '{applicant.job.title}' at {applicant.job.company_name} was updated to: {status_name}.",
                    action_url=request.build_absolute_uri(reverse_lazy("jobs:employee-my-applications")),
                    action_text="Track My Application"
                )
        except Exception:
            pass

    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("jobs:employer-dashboard-applicants", job_id=applicant.job.id)

