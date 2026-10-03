from django.apps import AppConfig


class JobsappConfig(AppConfig):
    name = "jobsapp"

    def ready(self):
        import jobsapp.signals  # noqa: F401
