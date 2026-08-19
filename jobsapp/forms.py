from datetime import datetime
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from jobsapp.models import (
    Applicant, Job, ApplicantProfile, Education, WorkExperience, CandidateSkill
)
from accounts.models import Company


class CreateJobForm(forms.ModelForm):
    class Meta:
        model = Job
        exclude = ("user", "created_at", "filled", "company", "status")
        widgets = {
            "last_date": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 5, "class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.Select(attrs={"class": "form-control"}),
            "type": forms.Select(attrs={"class": "form-control"}),
            "experience_level": forms.Select(attrs={"class": "form-control"}),
            "work_mode": forms.Select(attrs={"class": "form-control"}),
            "company_name": forms.TextInput(attrs={"class": "form-control"}),
            "company_description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "website": forms.TextInput(attrs={"class": "form-control"}),
            "salary": forms.NumberInput(attrs={"class": "form-control"}),
            "salary_max": forms.NumberInput(attrs={"class": "form-control"}),
            "currency": forms.TextInput(attrs={"class": "form-control"}),
            "vacancy": forms.NumberInput(attrs={"class": "form-control"}),
        }
        labels = {
            "last_date": "Application Deadline",
            "company_name": "Company Name",
            "company_description": "Company Description",
            "salary": "Minimum Salary (ETB)",
            "salary_max": "Maximum Salary (ETB)",
        }

    def clean_last_date(self):
        date = self.cleaned_data.get("last_date")
        if date and date.date() < timezone.now().date():
            raise ValidationError("Deadline cannot be in the past.")
        return date

    def clean_tags(self):
        tags = self.cleaned_data.get("tags")
        if tags and len(tags) > 6:
            raise forms.ValidationError("You can't add more than 6 tags")
        return tags

    def save(self, commit=True):
        job = super(CreateJobForm, self).save(commit=False)
        if commit:
            job.save()
            if "tags" in self.cleaned_data:
                for tag in self.cleaned_data["tags"]:
                    job.tags.add(tag)
        return job


class ApplyJobForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = ("job", "comment", "cv")
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": "Optional message to employer..."}),
        }


class ApplicantProfileForm(forms.ModelForm):
    class Meta:
        model = ApplicantProfile
        fields = ("title", "bio", "location", "cv_file", "github_link", "linkedin_link", "website")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Senior Python / Django Developer"}),
            "bio": forms.Textarea(attrs={"rows": 4, "class": "form-control", "placeholder": "Brief summary of your professional background..."}),
            "location": forms.Select(attrs={"class": "form-control"}),
            "cv_file": forms.FileInput(attrs={"class": "form-control-file"}),
            "github_link": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://github.com/username"}),
            "linkedin_link": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://linkedin.com/in/username"}),
            "website": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://yourwebsite.com"}),
        }


class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ("institution", "degree", "field_of_study", "start_date", "end_date", "is_current")
        widgets = {
            "institution": forms.TextInput(attrs={"class": "form-control"}),
            "degree": forms.TextInput(attrs={"class": "form-control"}),
            "field_of_study": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "is_current": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkExperience
        fields = ("title", "company", "location", "start_date", "end_date", "is_current", "description")
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "company": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "is_current": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }


class CandidateSkillForm(forms.ModelForm):
    class Meta:
        model = CandidateSkill
        fields = ("name", "level")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Python, Django, PostgreSQL"}),
            "level": forms.Select(attrs={"class": "form-control"}),
        }


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ("name", "logo", "description", "website", "location", "established_date")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "logo": forms.FileInput(attrs={"class": "form-control-file"}),
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "established_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }
