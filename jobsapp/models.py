from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta
import uuid

from accounts.models import User, Company
from tags.models import Tag

from .manager import JobManager

JOB_TYPE = (("1", "Full time"), ("2", "Part time"), ("3", "Internship"))

EXPERIENCE_LEVEL_CHOICES = (
    ("fresh", "Fresh Graduate"),
    ("entry", "Entry Level"),
    ("mid", "Mid Level"),
    ("senior", "Senior Level"),
    ("executive", "Executive"),
)

WORK_MODE_CHOICES = (
    ("on-site", "On-site"),
    ("remote", "Remote"),
    ("hybrid", "Hybrid"),
)

ETHIOPIAN_LOCATIONS = (
    ("Addis Ababa", "Addis Ababa"),
    ("Hawassa", "Hawassa"),
    ("Dire Dawa", "Dire Dawa"),
    ("Bahir Dar", "Bahir Dar"),
    ("Mekelle", "Mekelle"),
    ("Adama", "Adama"),
    ("Gondar", "Gondar"),
    ("Jimma", "Jimma"),
    ("Bishoftu", "Bishoftu"),
    ("Dessie", "Dessie"),
    ("Remote", "Remote"),
    ("Other", "Other"),
)

JOB_STATUS_CHOICES = (
    ("approved", "Approved"),
    ("pending", "Pending Approval"),
    ("rejected", "Rejected"),
)

APPLICANT_STATUS_CHOICES = (
    (1, "Pending"),
    (2, "Shortlisted"),
    (3, "Interview"),
    (4, "Accepted"),
    (5, "Rejected"),
)


def default_deadline():
    return timezone.now() + timedelta(days=30)


class Job(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="jobs")
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True, null=True, db_index=True)
    description = models.TextField()
    location = models.CharField(max_length=150, default="Addis Ababa")
    type = models.CharField(choices=JOB_TYPE, max_length=10)
    category = models.CharField(max_length=100)
    last_date = models.DateTimeField(default=default_deadline)
    company_name = models.CharField(max_length=100)
    company_description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to="job_logos/", blank=True, null=True, help_text="Company logo or vacancy screenshot")
    website = models.CharField(max_length=100, default="", blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    filled = models.BooleanField(default=False, db_index=True)
    salary = models.IntegerField(default=0, blank=True)
    salary_max = models.IntegerField(default=0, blank=True, null=True)
    currency = models.CharField(max_length=10, default="ETB")
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default="fresh")
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, default="on-site")
    status = models.CharField(max_length=20, choices=JOB_STATUS_CHOICES, default="approved", db_index=True)
    tags = models.ManyToManyField(Tag, blank=True)
    vacancy = models.IntegerField(default=1)
    is_featured = models.BooleanField(default=False, db_index=True)
    featured_until = models.DateTimeField(blank=True, null=True)

    objects = JobManager()

    class Meta:
        ordering = ["-id"]

    def _generate_unique_slug(self):
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        while Job.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        if self.slug:
            return reverse("jobs:jobs-detail-slug", kwargs={"slug": self.slug})
        return reverse("jobs:jobs-detail", kwargs={"id": self.id})

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        return timezone.now() > self.last_date

    @property
    def total_applicants(self):
        return self.applicants.count()

    @property
    def get_logo_url(self):
        if self.logo:
            try:
                return self.logo.url
            except Exception:
                pass
        first_img = self.images.first()
        if first_img and first_img.image:
            try:
                return first_img.image.url
            except Exception:
                pass
        return None

    @property
    def company_initials(self):
        name = (self.company_name or "").strip()
        if not name:
            return "JO"
        parts = name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return name[:2].upper()


class JobImage(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="job_screenshots/")
    caption = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Image for {self.job.title} (#{self.id})"


EXPERIENCE_YEARS_CHOICES = (
    ("0-1", "Less than 1 year (Fresh Graduate)"),
    ("1-2", "1 - 2 years (Junior)"),
    ("3-5", "3 - 5 years (Mid-Level)"),
    ("6-8", "6 - 8 years (Senior)"),
    ("9+", "9+ years (Lead / Executive)"),
)

NOTICE_PERIOD_CHOICES = (
    ("immediate", "Immediately available"),
    ("1_week", "1 week"),
    ("2_weeks", "2 weeks"),
    ("1_month", "1 month"),
    ("2_months", "2+ months"),
)

EDUCATION_LEVEL_CHOICES = (
    ("high_school", "High School / Secondary"),
    ("tvet_diploma", "TVET / Diploma"),
    ("bachelor", "Bachelor's Degree (BSc/BA)"),
    ("master", "Master's Degree (MSc/MA/MBA)"),
    ("phd", "Doctorate / Medical (PhD/MD)"),
    ("other", "Other / Professional Certificate"),
)


class Applicant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applicants")
    created_at = models.DateTimeField(default=timezone.now)
    comment = models.TextField(blank=True, null=True, help_text="Cover letter or candidate pitch")
    status = models.SmallIntegerField(choices=APPLICANT_STATUS_CHOICES, default=1)
    cv = models.FileField(upload_to="applications/", blank=True, null=True)
    interview_date = models.DateTimeField(blank=True, null=True)
    interview_location = models.CharField(max_length=255, blank=True, null=True)
    interview_notes = models.TextField(blank=True, null=True)

    # Real-World LinkedIn/Workday Application Attributes
    expected_salary = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. 25,000 ETB / month")
    experience_years = models.CharField(max_length=50, blank=True, null=True, help_text="Years of professional experience")
    notice_period = models.CharField(max_length=50, blank=True, null=True, help_text="Availability / notice period")
    education_level = models.CharField(max_length=100, blank=True, null=True, help_text="Highest education level")
    portfolio_link = models.URLField(blank=True, null=True, help_text="LinkedIn, GitHub, or Portfolio URL")
    ai_match_score = models.IntegerField(default=0, help_text="AI job match score at application time (0-100)")
    recruiter_rating = models.PositiveSmallIntegerField(default=0, help_text="Recruiter scorecard evaluation (0 to 5 stars)")
    recruiter_notes = models.TextField(blank=True, null=True, help_text="Internal recruiter notes on this candidate")

    class Meta:
        ordering = ["-id"]
        unique_together = ["user", "job"]

    def __str__(self):
        return self.user.get_full_name()

    @property
    def get_status(self):
        status_map = {
            1: "Pending",
            2: "Shortlisted",
            3: "Interview",
            4: "Accepted",
            5: "Rejected",
        }
        return status_map.get(self.status, "Pending")


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="favorites")
    created_at = models.DateTimeField(default=timezone.now)
    soft_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.job.title


class ApplicantProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="applicant_profile")
    title = models.CharField(max_length=150, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=150, choices=ETHIOPIAN_LOCATIONS, default="Addis Ababa")
    cv_file = models.FileField(upload_to="resumes/uploads/", blank=True, null=True)
    github_link = models.URLField(blank=True, null=True)
    linkedin_link = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    expected_salary = models.CharField(max_length=50, blank=True, null=True)
    experience_years = models.CharField(max_length=50, blank=True, null=True)
    notice_period = models.CharField(max_length=50, blank=True, null=True)
    education_level = models.CharField(max_length=100, blank=True, null=True)
    is_open_to_work = models.BooleanField(default=True, help_text="Open to Work badge for recruiters")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.email}"

    @property
    def completion_percentage(self):
        score = 0
        total_parts = 8
        if self.user.first_name and self.user.last_name:
            score += 1
        if self.title:
            score += 1
        if self.bio:
            score += 1
        if self.user.educations.exists():
            score += 1
        if self.user.skills.exists():
            score += 1
        if self.user.experiences.exists():
            score += 1
        if self.cv_file:
            score += 1
        if self.expected_salary or self.experience_years:
            score += 1
        return int((score / total_parts) * 100)


class Education(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="educations")
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=150)
    field_of_study = models.CharField(max_length=150, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.degree} at {self.institution}"


class WorkExperience(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="experiences")
    title = models.CharField(max_length=150)
    company = models.CharField(max_length=150)
    location = models.CharField(max_length=150, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.title} at {self.company}"


class CandidateSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=100)
    level = models.CharField(
        max_length=20,
        choices=(("beginner", "Beginner"), ("intermediate", "Intermediate"), ("expert", "Expert")),
        default="intermediate",
    )

    class Meta:
        unique_together = ["user", "name"]

    def __str__(self):
        return self.name


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.user.email}: {self.title}"


def create_notification(user, title, message, link=None):
    if user:
        try:
            return Notification.objects.create(
                user=user,
                title=title,
                message=message,
                link=link
            )
        except Exception:
            pass
    return None



class AdminAuditLog(models.Model):
    admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="admin_audit_logs")
    action = models.CharField(max_length=100, db_index=True)
    target_repr = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        admin_email = self.admin_user.email if self.admin_user else "System"
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {admin_email}: {self.action} -> {self.target_repr}"


class JobAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="job_alerts", null=True, blank=True)
    email = models.EmailField()
    category = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=150, blank=True, null=True)
    keywords = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Job Alert for {self.email} ({self.category or 'All'} in {self.location or 'All'})"


class Conversation(models.Model):
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="employer_conversations")
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name="candidate_conversations")
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = ("employer", "candidate", "job")

    def __str__(self):
        job_title = f" ({self.job.title})" if self.job else ""
        emp_name = self.employer.get_full_name() or self.employer.email
        cand_name = self.candidate.get_full_name() or self.candidate.email
        return f"{emp_name} <-> {cand_name}{job_title}"

    def unread_count(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def get_other_user(self, user):
        return self.candidate if user == self.employer else self.employer


class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_chat_messages")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Msg from {self.sender.email} at {self.created_at:%H:%M}"


