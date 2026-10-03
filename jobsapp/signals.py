import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Job
from .utils.telegram import broadcast_job_to_telegram

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Job)
def notify_telegram_on_job_creation(sender, instance, created, **kwargs):
    """
    Automatically broadcasts newly created job to Telegram Channel/Bot when saved.
    """
    if created and instance.status == "approved":
        try:
            success = broadcast_job_to_telegram(instance)
            if success:
                logger.info(f"Successfully broadcasted job {instance.id} '{instance.title}' to Telegram.")
            else:
                logger.warning(f"Failed to broadcast job {instance.id} to Telegram.")
        except Exception as e:
            logger.error(f"Error broadcasting job {instance.id} to Telegram: {e}")
