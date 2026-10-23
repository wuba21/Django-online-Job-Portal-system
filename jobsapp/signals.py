import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Job
from .utils.telegram import broadcast_job_to_telegram

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Job)
def notify_telegram_on_job_creation(sender, instance, created, **kwargs):
    """
    Automatic Telegram posting on save is disabled per administrator preference.
    Admins can explicitly broadcast vacancies using the 'Broadcast to Telegram' action
    in the admin dashboard or details page.
    """
    pass

