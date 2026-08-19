import json
import os
from urllib.parse import urlparse

from django.contrib.auth.decorators import login_required
from django.templatetags.static import static
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView
from django.utils.text import get_valid_filename

import io

from jobsapp.decorators import user_is_employee

# Create your views here.
from jobsapp.mixins import EmployeeRequiredMixin
from resume_cv.forms import ResumeCvForm
from resume_cv.models import ResumeCvTemplate, ResumeCvCategory, ResumeCv


class TemplateListView(ListView):
    """
    Get list of templates to create resume/cv
    """

    model = ResumeCvTemplate
    context_object_name = "templates"
    template_name = "resumes/templates.html"

    def get_queryset(self):
        category_id = self.request.GET.get("category")
        if category_id and category_id.isdigit():
            return self.model.objects.filter(category_id=category_id, active=True)
        return self.model.objects.filter(active=True)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["categories"] = ResumeCvCategory.objects.all()
        return data


class ResumeCVCreateView(LoginRequiredMixin, EmployeeRequiredMixin, View):
    """
    Create resume/cv
    """

    form_class = ResumeCvForm

    def post(self, request):
        f = ResumeCvForm(request.POST)
        if f.is_valid():
            f.instance.user = request.user
            r = f.save()
            return redirect(reverse_lazy("resume_cv:builder", kwargs={"code": r.code}))
        else:
            print(f.errors)
            return redirect(reverse_lazy("resume_cv:templates"))


def resume_builder(request, code):
    """
    Resume builder
    """
    resume = ResumeCv.objects.get(code=code)
    templates = ResumeCvTemplate.objects.all()
    token = get_token(request)
    return render(request, "resumes/builder.html", {"resume": resume, "templates": templates, "token": token})


@csrf_exempt
def update_builder(request, id):
    """
    Resume builder
    """
    resume = ResumeCv.objects.get(id=id)
    if resume:
        data = json.loads(request.body)
        resume.content = data.get("gjs-html")
        resume.style = data.get("gjs-css")
        resume.save()
        return JsonResponse(
            {
                "success": "Updated successfully",
            },
            safe=True,
        )
    return JsonResponse(
        {
            "error": "No resume found",
        },
        safe=True,
    )


def load_builder(request, id):
    """
    Load builder
    """
    resume = ResumeCv.objects.get(id=id)
    if resume:
        return JsonResponse(
            {
                "gjs-html": resume.content if resume.content else resume.template.content,
                "gjs-css": resume.style if resume.style else resume.template.style,
            },
            safe=True,
        )
    else:
        return JsonResponse(
            {
                "error": "No template found",
            },
            safe=True,
        )

ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB

@csrf_exempt
def upload_image(request):
    if request.method == 'POST' and request.FILES:
        fs = FileSystemStorage()
        urls = []
        for key in request.FILES:
            for file in request.FILES.getlist(key):
                # Validate file extension
                ext = os.path.splitext(file.name.lower())[-1]
                if ext not in ALLOWED_IMAGE_EXTENSIONS:
                    return JsonResponse({'error': f'Invalid file type: {ext}. Allowed: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}'}, status=400)
                # Validate file size
                if file.size > MAX_UPLOAD_SIZE:
                    return JsonResponse({'error': 'File too large. Max size is 5MB'}, status=400)
                # Sanitize filename to prevent path traversal
                safe_filename = get_valid_filename(file.name)
                filename = fs.save('resumes/' + safe_filename, file)
                urls.append({"src": fs.url(filename)})
        return JsonResponse({"data": urls}, safe=False)
    return JsonResponse({'error': 'No file uploaded'}, status=400)


class UserResumeListView(ListView):
    model = ResumeCv
    template_name = "resumes/user_resumes.html"
    context_object_name = "resumes"

    def get_queryset(self):
        return self.model.objects.filter(user_id=self.request.user.id).order_by("-id")


@login_required
@user_is_employee
def download_resume(request, id):
    resume = ResumeCv.objects.get(id=id)
    if resume:
        # Include Font Awesome for icons, Noto Sans for Unicode support (Amharic, Oromo, Tigrinya)
        html_string = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Ethiopic:wght@400;700&display=swap');
                body {{ font-family: 'Noto Sans Ethiopic', sans-serif; margin:0; padding:0; }}
                {resume.style}
            </style>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        </head>
        <body>
            {resume.content}
        </body>
        </html>
        """
        
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_content(html_string, wait_until="load")
                
                # Generate PDF (A4 format)
                pdf_bytes = page.pdf(format="A4", print_background=True, margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"})
                browser.close()
                
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{resume.name}.pdf"'
            return response
        except Exception as e:
            import logging
            logging.error("PDF generation failed. Error: %s", repr(e))
            # Fallback to HTML print view
            return HttpResponse(html_string, content_type="text/html")
            
    return redirect("resume_cv:resumes")
