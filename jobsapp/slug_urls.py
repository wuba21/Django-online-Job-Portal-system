"""
Root-level SEO slug URL resolver for Job posts.
Enables URLs like: ethiojobs.com/ethiopian-airlines-group-vacancy-2026/
"""
from django.urls import path
from jobsapp.views.home import JobDetailsView

urlpatterns = [
    path("", JobDetailsView.as_view(), name="job-slug-root"),
]
