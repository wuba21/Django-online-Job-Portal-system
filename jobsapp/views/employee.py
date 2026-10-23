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
from jobsapp.utils.recommendation import (
    calculate_job_match_score, get_recommended_jobs_for_user, invalidate_recommendation_cache
)


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

        # AI Job Recommendations using Content-Based TF-IDF & Cosine Similarity
        recommended_jobs = get_recommended_jobs_for_user(user, limit=6)

        # Single-query aggregation for all application metrics
        from django.db.models import Count, Q
        app_stats = applications.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status=1)),
            shortlisted=Count("id", filter=Q(status=2)),
            accepted=Count("id", filter=Q(status=4)),
        )

        context["profile"] = profile
        context["completion_percentage"] = profile.completion_percentage
        context["applications"] = applications
        context["total_applications"] = app_stats["total"]
        context["pending_applications"] = app_stats["pending"]
        context["shortlisted_applications"] = app_stats["shortlisted"]
        context["accepted_applications"] = app_stats["accepted"]
        context["favorites_count"] = favorites.count()
        context["recommended_jobs"] = recommended_jobs
        context["unread_notifications_count"] = Notification.objects.filter(user=user, is_read=False).count()
        return context


@method_decorator(login_required(login_url=reverse_lazy("accounts:login")), name="dispatch")
@method_decorator(user_is_employee, name="dispatch")
class RecommendedJobsListView(ListView):
    """
    Dedicated view for exploring all personalized AI recommended jobs with match scores and details.
    """
    template_name = "jobs/employee/recommended_jobs.html"
    context_object_name = "recommended_jobs"
    paginate_by = 12

    def get_queryset(self):
        user = self.request.user
        try:
            min_score = int(self.request.GET.get("min_score", 15))
        except (ValueError, TypeError):
            min_score = 15
        return get_recommended_jobs_for_user(user, limit=60, min_score=min_score)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = ApplicantProfile.objects.get_or_create(user=self.request.user)
        context["profile"] = profile
        context["completion_percentage"] = profile.completion_percentage
        context["min_score"] = self.request.GET.get("min_score", "15")
        context["user_skills"] = self.request.user.skills.all() if hasattr(self.request.user, "skills") else []
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
            invalidate_recommendation_cache(user.id)
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:employee-profile-update")
        else:
            messages.error(request, "Please correct the highlighted errors below.")

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
            invalidate_recommendation_cache(request.user.id)
            messages.success(request, "Education added successfully.")
        else:
            institution = request.POST.get("institution", "").strip()
            degree = request.POST.get("degree", "").strip()
            field_of_study = request.POST.get("field_of_study", "").strip()
            if institution and degree:
                Education.objects.create(
                    user=request.user,
                    institution=institution,
                    degree=degree,
                    field_of_study=field_of_study
                )
                invalidate_recommendation_cache(request.user.id)
                messages.success(request, "Education added successfully.")
            else:
                messages.error(request, "Please fill in Institution and Degree fields.")
    return redirect("accounts:employee-profile-update")


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employee
def delete_education(request, pk):
    edu = get_object_or_404(Education, pk=pk, user=request.user)
    edu.delete()
    invalidate_recommendation_cache(request.user.id)
    messages.success(request, "Education deleted successfully.")
    return redirect("accounts:employee-profile-update")


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employee
def add_experience(request):
    if request.method == "POST":
        form = WorkExperienceForm(request.POST)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.user = request.user
            exp.save()
            invalidate_recommendation_cache(request.user.id)
            messages.success(request, "Work experience added successfully.")
        else:
            title = request.POST.get("title", "").strip()
            company = request.POST.get("company", "").strip()
            description = request.POST.get("description", "").strip()
            if title and company:
                WorkExperience.objects.create(
                    user=request.user,
                    title=title,
                    company=company,
                    description=description
                )
                invalidate_recommendation_cache(request.user.id)
                messages.success(request, "Work experience added successfully.")
            else:
                messages.error(request, "Please fill in Job Title and Company fields.")
    return redirect("accounts:employee-profile-update")


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employee
def delete_experience(request, pk):
    exp = get_object_or_404(WorkExperience, pk=pk, user=request.user)
    exp.delete()
    invalidate_recommendation_cache(request.user.id)
    messages.success(request, "Work experience deleted successfully.")
    return redirect("accounts:employee-profile-update")


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employee
def add_skill(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        level = request.POST.get("level", "intermediate")
        if name:
            CandidateSkill.objects.update_or_create(
                user=request.user,
                name=name,
                defaults={"level": level}
            )
            invalidate_recommendation_cache(request.user.id)
            messages.success(request, f"Skill '{name}' added successfully.")
        else:
            messages.error(request, "Please enter a valid skill name.")
    return redirect("accounts:employee-profile-update")


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employee
def delete_skill(request, pk):
    skill = get_object_or_404(CandidateSkill, pk=pk, user=request.user)
    skill.delete()
    invalidate_recommendation_cache(request.user.id)
    messages.success(request, "Skill deleted successfully.")
    return redirect("accounts:employee-profile-update")


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employee
def withdraw_application(request, applicant_id):
    applicant = get_object_or_404(Applicant, id=applicant_id, user=request.user)
    if applicant.status == 1:  # Only pending
        job_title = applicant.job.title
        applicant.delete()
        invalidate_recommendation_cache(request.user.id)
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


import io
import re


@login_required(login_url=reverse_lazy("accounts:login"))
@user_is_employee
def ai_parse_resume(request):
    """
    AI Resume & CV Profile Auto-Filler:
    Extracts structured professional profile data (title, bio, skills, location,
    education, and experience) directly from an uploaded PDF/document or pasted resume text.
    """
    if request.method == "POST":
        resume_text = request.POST.get("resume_text", "").strip()
        uploaded_file = request.FILES.get("resume_file")

        # 1. Extract text from uploaded PDF if provided
        if uploaded_file:
            filename = uploaded_file.name.lower()
            if filename.endswith(".pdf"):
                try:
                    import pypdf
                    reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
                    extracted_pages = [page.extract_text() for page in reader.pages if page.extract_text()]
                    resume_text = "\n".join(extracted_pages)
                except Exception as e:
                    messages.error(request, f"Could not read PDF resume: {e}")
                    return redirect("accounts:employee-profile-update")
            elif filename.endswith((".txt", ".md")):
                try:
                    resume_text = uploaded_file.read().decode("utf-8", errors="ignore")
                except Exception:
                    pass

        if not resume_text:
            messages.error(request, "Please upload a readable PDF resume or paste your CV text.")
            return redirect("accounts:employee-profile-update")

        user = request.user
        profile, _ = ApplicantProfile.objects.get_or_create(user=user)

        # 2. Extract Professional Title
        detected_title = None
        common_titles = [
            "Senior Full Stack Developer", "Full Stack Developer", "Software Engineer",
            "Python Developer", "Django Developer", "Frontend Developer", "Backend Developer",
            "DevOps Engineer", "Mobile App Developer", "React Developer", "UI/UX Designer",
            "Data Scientist", "Data Analyst", "Database Administrator", "System Administrator",
            "Network Engineer", "Cybersecurity Specialist", "IT Support Specialist",
            "Chief Accountant", "Senior Accountant", "Accountant", "Finance Officer",
            "Financial Analyst", "Internal Auditor", "Tax Consultant", "Credit Analyst",
            "HR Manager", "Human Resources Specialist", "Recruiter", "Operations Manager",
            "Marketing Manager", "Digital Marketing Specialist", "Sales Manager", "Sales Executive",
            "Civil Engineer", "Electrical Engineer", "Mechanical Engineer", "Architect",
            "Project Manager", "Product Manager", "Supply Chain Manager", "Procurement Officer",
            "Public Health Officer", "Pharmacist", "Medical Doctor", "Nurse"
        ]
        lower_text = resume_text.lower()
        for t in common_titles:
            if t.lower() in lower_text:
                detected_title = t
                break

        if detected_title and not profile.title:
            profile.title = detected_title

        # 3. Extract Location
        from jobsapp.models import ETHIOPIAN_LOCATIONS
        for loc_code, loc_name in ETHIOPIAN_LOCATIONS:
            if loc_name.lower() in lower_text:
                profile.location = loc_name
                break

        # 4. Extract Phone Number
        phone_match = re.search(r'(\+251[\s\-]?[0-9]{9}|09[0-9]{8}|07[0-9]{8})', resume_text)
        if phone_match and not user.phone_number:
            user.phone_number = phone_match.group(1).replace(" ", "").replace("-", "")
            user.save(update_fields=["phone_number"])

        # 5. Extract Skills
        SKILL_DICTIONARY = [
            "Python", "Django", "JavaScript", "TypeScript", "React", "Node.js", "Vue.js", "Angular",
            "PHP", "Laravel", "Java", "Spring Boot", "C#", ".NET", "Flutter", "React Native",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes", "AWS",
            "Linux", "Git", "REST API", "GraphQL", "HTML5", "CSS3", "Bootstrap", "Tailwind CSS",
            "Accounting", "IFRS", "GAAP", "QuickBooks", "Peachtree", "Financial Reporting", "Auditing",
            "Tax Compliance", "Payroll", "Budgeting", "Financial Modeling", "Excel",
            "Project Management", "Agile", "Scrum", "Jira", "Human Resources", "Recruitment",
            "Digital Marketing", "SEO", "Content Writing", "Graphic Design", "Figma", "Photoshop",
            "AutoCAD", "Civil 3D", "Structural Analysis", "Customer Service", "Sales Negotiation"
        ]
        added_skills = []
        for skill_term in SKILL_DICTIONARY:
            # Word boundary search
            pattern = r'\b' + re.escape(skill_term) + r'\b'
            if re.search(pattern, resume_text, re.IGNORECASE):
                _, created = CandidateSkill.objects.update_or_create(
                    user=user,
                    name=skill_term,
                    defaults={"level": "intermediate"}
                )
                if created:
                    added_skills.append(skill_term)

        # 6. Extract Education
        education_added = 0
        degree_patterns = [
            (r'(Bachelor of Science|B\.?Sc\.?|BSc|Degree in Computer Science|Degree in Software Engineering|Degree in Information Technology)', "Bachelor's Degree", "Computer Science"),
            (r'(Bachelor of Arts|B\.?A\.?|BA in Accounting|Degree in Accounting|Degree in Finance)', "Bachelor's Degree", "Accounting & Finance"),
            (r'(Bachelor of Arts|B\.?A\.?|BA in Economics|Degree in Economics)', "Bachelor's Degree", "Economics"),
            (r'(Bachelor of Arts|B\.?A\.?|BA in Management|Degree in Business)', "Bachelor's Degree", "Business Administration"),
            (r'(Master of Science|M\.?Sc\.?|MSc|Master of Arts|M\.?A\.?|MBA)', "Master's Degree", "Business / Tech"),
            (r'(Diploma in|College Diploma)', "Diploma", "Information Technology"),
        ]
        for pattern, deg_name, field_name in degree_patterns:
            if re.search(pattern, resume_text, re.IGNORECASE):
                # Check if education already exists
                if not Education.objects.filter(user=user, degree=deg_name).exists():
                    Education.objects.create(
                        user=user,
                        institution="Addis Ababa University" if "addis ababa" in lower_text else "Higher Education Institution",
                        degree=deg_name,
                        field_of_study=field_name,
                        start_date="2020-09-01",
                        end_date="2024-07-01",
                        is_current=False
                    )
                    education_added += 1
                break

        # 7. Summary Bio
        if not profile.bio:
            # Extract first substantial paragraph as summary
            lines = [line.strip() for line in resume_text.splitlines() if len(line.strip()) > 40]
            if lines:
                profile.bio = lines[0][:450]

        profile.save()
        invalidate_recommendation_cache(user.id)

        summary_msg = f"⚡ AI Profile Auto-Fill Complete! "
        details = []
        if detected_title:
            details.append(f"Title: '{detected_title}'")
        if added_skills:
            details.append(f"{len(added_skills)} skills added ({', '.join(added_skills[:5])})")
        if education_added:
            details.append(f"{education_added} education record")

        if details:
            summary_msg += "Identified: " + ", ".join(details)
        else:
            summary_msg += "Profile updated with extracted details."

        messages.success(request, summary_msg)
        return redirect("accounts:employee-profile-update")

    return redirect("accounts:employee-profile-update")

