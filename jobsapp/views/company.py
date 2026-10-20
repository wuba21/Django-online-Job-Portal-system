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

        # Fetch verified company reviews
        reviews = company.reviews.filter(is_approved=True).select_related("user")
        total_rev = reviews.count()

        rating_breakdown = {}
        for star in range(5, 0, -1):
            count = reviews.filter(rating=star).count()
            pct = int((count / total_rev * 100)) if total_rev > 0 else 0
            rating_breakdown[star] = {"count": count, "percentage": pct}

        user_review = None
        if self.request.user.is_authenticated:
            user_review = company.reviews.filter(user=self.request.user).first()

        context["active_jobs"] = active_jobs
        context["total_active_jobs"] = active_jobs.count()
        context["reviews"] = reviews
        context["total_reviews"] = total_rev
        context["rating_breakdown"] = rating_breakdown
        context["user_review"] = user_review
        return context


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from accounts.models import CompanyReview
from jobsapp.models import create_notification


@login_required
def add_company_review(request, company_id):
    """
    Submits or updates a Glassdoor-style employee / candidate company review and rating.
    """
    company = get_object_or_404(Company, id=company_id)

    if request.user == company.user:
        messages.error(request, "Company owners cannot review their own company.")
        return redirect("jobs:company-detail", id=company.id)

    if request.method == "POST":
        try:
            rating = int(request.POST.get("rating", 5))
            rating = max(1, min(5, rating))
        except (ValueError, TypeError):
            rating = 5

        title = request.POST.get("title", "").strip()
        review_text = request.POST.get("review_text", "").strip()
        pros = request.POST.get("pros", "").strip()
        cons = request.POST.get("cons", "").strip()

        if not title or not review_text:
            messages.error(request, "Please provide a review headline and detailed comments.")
            return redirect("jobs:company-detail", id=company.id)

        review, created = CompanyReview.objects.update_or_create(
            company=company,
            user=request.user,
            defaults={
                "rating": rating,
                "title": title,
                "review_text": review_text,
                "pros": pros,
                "cons": cons,
                "is_approved": True,
            }
        )

        # Notify company owner
        if company.user:
            create_notification(
                user=company.user,
                title="⭐ New Company Review Received",
                message=f"{request.user.get_full_name() or 'A user'} gave your company a {rating}-star review: '{title}'",
                link=f"/companies/{company.id}/"
            )

        action_msg = "submitted" if created else "updated"
        messages.success(request, f"🎉 Thank you! Your review has been {action_msg} successfully.")

    return redirect("jobs:company-detail", id=company.id)
