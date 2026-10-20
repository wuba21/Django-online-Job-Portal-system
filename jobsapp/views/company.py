from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView

from accounts.models import Company
from jobsapp.models import ETHIOPIAN_LOCATIONS, Job


class CompanyListView(ListView):
    model = Company
    template_name = "jobs/companies/company_list.html"
    context_object_name = "companies"
    paginate_by = 12

    def get_queryset(self):
        from django.db.models import Case, IntegerField, Value, When
        queryset = Company.objects.annotate(
            active_jobs_count=Count("jobs", filter=Q(jobs__filled=False, jobs__status="approved")),
            is_verified_order=Case(
                When(license_status="verified", then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by("-is_verified_order", "-active_jobs_count", "-id")

        q = self.request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q) |
                Q(industry__icontains=q) |
                Q(location__icontains=q)
            )

        industry = self.request.GET.get("industry")
        if industry and industry != "all":
            queryset = queryset.filter(industry__iexact=industry)

        location = self.request.GET.get("location")
        if location and location != "all":
            queryset = queryset.filter(location__icontains=location)

        verified = self.request.GET.get("verified")
        if verified == "1":
            queryset = queryset.filter(license_status="verified")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["locations"] = ETHIOPIAN_LOCATIONS
        context["industries"] = [
            "Information Technology & Software",
            "Banking & Financial Services",
            "Non-Governmental Organization (NGO)",
            "Telecommunications",
            "Healthcare & Pharmaceuticals",
            "Engineering & Construction",
            "Manufacturing & Industry",
            "Education & Training",
            "Logistics, Transport & Supply Chain",
            "Hospitality & Tourism",
        ]
        context["selected_q"] = self.request.GET.get("q", "")
        context["selected_industry"] = self.request.GET.get("industry", "all")
        context["selected_location"] = self.request.GET.get("location", "all")
        context["selected_verified"] = self.request.GET.get("verified", "")
        context["total_companies_count"] = Company.objects.count()
        context["verified_companies_count"] = Company.objects.filter(license_status="verified").count()
        return context


class CompanyDetailView(DetailView):
    model = Company
    template_name = "jobs/companies/company_detail.html"
    context_object_name = "company"
    pk_url_kwarg = "id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.object

        # Fetch active vacancies for this company
        active_jobs = Job.objects.filter(
            Q(company=company) | Q(company_name__iexact=company.name),
            filled=False,
            status="approved"
        ).order_by("-is_featured", "-created_at")

        context["active_jobs"] = active_jobs
        context["total_active_jobs"] = active_jobs.count()
        return context
