from django.db.models import Q
from django.shortcuts import render
from categories.models import Category
from jobsapp.models import ETHIOPIAN_LOCATIONS, Job


def telegram_webapp_view(request):
    """
    Telegram Mini-App (TMA) Mobile Web Portal:
    Optimized for Telegram's in-app webview container. Automatically adapts to
    Telegram's dark/light native theme and enables fast vacancy browsing.
    """
    jobs = (
        Job.objects.filter(filled=False, status="approved")
        .select_related("user", "company")
        .order_by("-is_featured", "-created_at")
    )

    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    location = request.GET.get("location", "")

    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) |
            Q(company_name__icontains=q) |
            Q(description__icontains=q)
        )
    if category and category != "all":
        jobs = jobs.filter(category__id=category)
    if location and location != "all":
        jobs = jobs.filter(location__icontains=location)

    context = {
        "jobs": jobs[:30],
        "categories": Category.objects.all(),
        "locations": ETHIOPIAN_LOCATIONS,
        "selected_q": q,
        "selected_category": category,
        "selected_location": location,
        "total_count": jobs.count(),
    }
    return render(request, "jobs/telegram/webapp.html", context)
