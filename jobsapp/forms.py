from datetime import datetime
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from jobsapp.models import (
    Applicant, Job, ApplicantProfile, Education, WorkExperience, CandidateSkill
)
from accounts.models import Company
from tags.models import Tag


class CreateJobForm(forms.ModelForm):
    tags = forms.MultipleChoiceField(required=False)

    class Meta:
        model = Job
        exclude = ("user", "created_at", "filled", "company", "status")
        widgets = {
            "last_date": forms.DateTimeInput(attrs={"type": "date", "class": "form-control"}),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            tag_choices = [(str(t.id), t.name) for t in Tag.objects.all()]
            # Include custom submitted values if any
            if self.data and "tags" in self.data:
                if hasattr(self.data, "getlist"):
                    extra = self.data.getlist("tags")
                else:
                    extra = self.data.get("tags")
                    if not isinstance(extra, (list, tuple)):
                        extra = [extra]
                for val in extra:
                    if val and not any(str(val) == choice[0] for choice in tag_choices):
                        tag_choices.append((str(val), str(val)))
            self.fields["tags"].choices = tag_choices
        except Exception:
            self.fields["tags"].choices = []
        self.fields["tags"].required = False
        self.fields["salary"].required = False
        self.fields["salary_max"].required = False
        self.fields["experience_level"].required = False
        self.fields["work_mode"].required = False
        self.fields["currency"].required = False
        self.fields["company_description"].required = False
        self.fields["website"].required = False
        self.fields["vacancy"].required = False

    def clean_salary(self):
        salary = self.cleaned_data.get("salary")
        if salary is None or salary == "":
            return 0
        return salary

    def clean_salary_max(self):
        salary_max = self.cleaned_data.get("salary_max")
        if salary_max is None or salary_max == "":
            return 0
        return salary_max

    def clean_experience_level(self):
        val = self.cleaned_data.get("experience_level")
        return val if val else "fresh"

    def clean_work_mode(self):
        val = self.cleaned_data.get("work_mode")
        return val if val else "on-site"

    def clean_currency(self):
        val = self.cleaned_data.get("currency")
        return val if val else "ETB"

    def clean_vacancy(self):
        val = self.cleaned_data.get("vacancy")
        return val if val else 1

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
            if hasattr(self.data, "getlist"):
                raw_tags = self.data.getlist("tags")
            else:
                raw_tags = self.data.get("tags")
                if isinstance(raw_tags, str):
                    raw_tags = [raw_tags]
            if raw_tags:
                job.tags.clear()
                for tag_val in raw_tags[:6]:
                    tag_val = str(tag_val).strip()
                    if not tag_val:
                        continue
                    if tag_val.isdigit():
                        try:
                            tag_obj = Tag.objects.get(id=int(tag_val))
                            job.tags.add(tag_obj)
                        except Tag.DoesNotExist:
                            tag_obj, _ = Tag.objects.get_or_create(name=tag_val)
                            job.tags.add(tag_obj)
                    else:
                        tag_obj, _ = Tag.objects.get_or_create(name=tag_val)
                        job.tags.add(tag_obj)
            elif "tags" in self.cleaned_data:
                job.tags.set(self.cleaned_data["tags"])
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
