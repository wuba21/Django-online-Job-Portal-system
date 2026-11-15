from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse


class ChangeFreq:
    """
    https://www.sitemaps.org/de/protocol.html#changefreqdef
    """

    always = "always"
    hourly = "hourly"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"
    never = "never"


class StaticViewSitemap(Sitemap):
    i18n = True
    name = ""

    def items(self):
        return [self.name]

    def location(self, item):
        return reverse(item)


class SitemapBase(Sitemap):
    """
    Base class for sitemap
    """

    name = ""

    def items(self):
        return [self.name]

    def location(self, item):
        return reverse(item)


class Sitemaps:
    """
    https://docs.djangoproject.com/en/3.1/ref/contrib/sitemaps/
    """

    class Home(SitemapBase):
        i18n = True
        name = "jobs:home"
        changefreq = ChangeFreq.weekly

    class Search(SitemapBase):
        i18n = True
        name = "jobs:search"
        changefreq = ChangeFreq.weekly

    class Favorite(SitemapBase):
        i18n = True
        name = "jobs:favorite"
        changefreq = ChangeFreq.weekly

    class Jobs(SitemapBase):
        i18n = True
        name = "jobs:jobs"
        changefreq = ChangeFreq.weekly

    class JobDetails(Sitemap):
        i18n = True
        changefreq = ChangeFreq.daily
        priority = 0.9

        def items(self):
            from jobsapp.models import Job
            return Job.objects.filter(status="approved", filled=False).order_by("-created_at")

        def location(self, item):
            return reverse("jobs:jobs-detail", kwargs={"id": item.id})

        def lastmod(self, item):
            return item.created_at

    def __iter__(self):
        # Return all members of the SitemapType
        for item in dir(self):
            member = getattr(self, item)
            if isinstance(member, type) and issubclass(member, Sitemap):
                yield member.__name__, member()

