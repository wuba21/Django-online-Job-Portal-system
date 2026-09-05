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
from jobsapp.decorators import user_is_employer
from jobsapp.forms import CompanyForm, CreateJobForm
from jobsapp.models import Applicant, Job
from jobsapp.utils.notifications import create_notification, send_event_email
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
    paginate_by = 6

    @method_decorator(login_required(login_url=reverse_lazy("accounts:login")))
    @method_decorator(user_is_employer)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(self.request, *args, **kwargs)

    def get_queryset(self):
        job = get_object_or_404(Job, id=self.kwargs["job_id"], user=self.request.user)
        queryset = Applicant.objects.filter(job=job).order_by("id")
        status_param = self.request.GET.get("status")
        if status_param and status_param.isdigit():
            queryset = queryset.filter(status=int(status_param))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["job"] = get_object_or_404(Job, id=self.kwargs["job_id"], user=self.request.user)
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
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        company, _ = Company.objects.get_or_create(
            user=self.request.user,
            defaults={"name": form.cleaned_data.get("company_name", "Company")}
        )
        form.instance.company = company
        response = super(JobCreateView, self).form_valid(form)

        # Broadcast new vacancy alert directly to Telegram Channel
        try:
            from jobsapp.utils.telegram import broadcast_job_to_telegram
            broadcast_job_to_telegram(self.object)
        except Exception as e:
            print(f"Telegram broadcast error on create: {e}")

        messages.success(self.request, "Job posted successfully.")
        return response


@method_decorator(login_required(login_url=reverse_lazy("accounts:login")), name="dispatch")
@method_decorator(user_is_employer, name="dispatch")
class JobUpdateView(UpdateView):
    template_name = "jobs/update.html"
    form_class = CreateJobForm
    extra_context = {"title": "Edit Job"}
    slug_field = "id"
    slug_url_kwarg = "id"
    success_url = reverse_lazy("jobs:employer-dashboard")
    context_object_name = "job"

    def get_queryset(self):
        return Job.objects.filter(user_id=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tags"] = Tag.objects.all()
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Job updated successfully.")
        return super(JobUpdateView, self).form_valid(form)


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employer
def delete_employer_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, user=request.user)
    title = job.title
    job.delete()
    messages.success(request, f"Job '{title}' deleted successfully.")
    return redirect("jobs:employer-dashboard")


class ApplicantsListView(ListView):
    model = Applicant
    template_name = "jobs/employer/all-applicants.html"
    context_object_name = "applicants"

    @method_decorator(login_required(login_url=reverse_lazy("accounts:login")))
    @method_decorator(user_is_employer)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(self.request, *args, **kwargs)

    def get_queryset(self):
        self.queryset = self.model.objects.filter(job__user_id=self.request.user.id).order_by("-id")
        status_param = self.request.GET.get("status")
        if status_param and status_param.isdigit():
            self.queryset = self.queryset.filter(status=int(status_param))
        return self.queryset


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
        return Applicant.objects.select_related("job", "user").filter(job__user=self.request.user)


@method_decorator(login_required(login_url=reverse_lazy("accounts:login")), name="dispatch")
@method_decorator(user_is_employer, name="dispatch")
class SendResponseView(UpdateView):
    model = Applicant
    http_method_names = ["post"]
    pk_url_kwarg = "applicant_id"
    fields = ("status", "comment")

    def get_queryset(self):
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
        create_notification(
            user=self.object.user,
            title=f"Application Update: {self.object.job.title}",
            message=f"Your application status for '{self.object.job.title}' has been updated to '{status_name}'.",
            link=reverse_lazy("jobs:employee-my-applications")
        )

        send_event_email(
            user_email=self.object.user.email,
            subject=f"Job Application Update - {self.object.job.title}",
            message=f"Hello {self.object.user.get_full_name() or 'Candidate'},\n\nYour application status for the position '{self.object.job.title}' at {self.object.job.company_name} has been updated to: {status_name}.\n\nComment from employer: {self.object.comment or 'None'}\n\nLog in to your dashboard to view details."
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
            return redirect("jobs:employer-dashboard")

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
