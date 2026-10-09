from django.urls import re_path
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.flatpages import views as flatpages_views
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.conf.urls.static import static
from django.views.i18n import set_language
from django.views.decorators.csrf import csrf_exempt
import importlib.util

try:
    from drf_yasg import openapi
    from drf_yasg.views import get_schema_view
    from rest_framework import permissions
    schema_view = get_schema_view(
        openapi.Info(
            title="Jobs Portal API",
            default_version="v1",
            description="Jobs Portal Api Description",
            terms_of_service="https://www.google.com/policies/terms/",
            contact=openapi.Contact(email="contact@snippets.local"),
            license=openapi.License(name="BSD License"),
        ),
        public=True,
        permission_classes=(permissions.AllowAny,),
    )
    HAS_DRF_YASG = True
except ImportError:
    HAS_DRF_YASG = False

try:
    from graphene_file_upload.django import FileUploadGraphQLView
    HAS_GRAPHQL = True
except ImportError:
    HAS_GRAPHQL = False

from jobs.sitemaps import Sitemaps, StaticViewSitemap

lang_patterns = i18n_patterns(
    path("", include("jobsapp.urls")),
    path("", include("accounts.urls")),
    path("", include("resume_cv.urls")),
    path("payments/", include("payments.urls")),
)

api_patterns = [
    path("", include("accounts.api.urls")),
    path("", include("jobsapp.api.urls")),
    path("", include("tags.api.urls")),
]

if HAS_DRF_YASG:
    api_patterns.insert(0, path("swagger", schema_view.with_ui("swagger", cache_timeout=0)))

if importlib.util.find_spec("categories") is not None:
    api_patterns.append(path("", include("categories.urls")))

urlpatterns = lang_patterns + [
    path("i18n/setlang/", set_language, name="set_language"),
    re_path(r"^i18n/", include("django.conf.urls.i18n")),
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),
    path("sitemap.xml/", sitemap, {"sitemaps": dict(Sitemaps())}, name="django.contrib.sitemaps.views.sitemap"),
]

if importlib.util.find_spec("social_django") is not None:
    urlpatterns.append(path("social-auth/", include("social_django.urls", namespace="social")))

if HAS_GRAPHQL:
    urlpatterns.append(path("graphql/", csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True))))

urlpatterns.append(path("<slug:slug>/", include("jobsapp.slug_urls")))

if settings.ENABLE_PROMETHEUS:
    urlpatterns.append(path("", include("django_prometheus.urls")))

if bool(settings.DEBUG):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
