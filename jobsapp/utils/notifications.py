from django.core.mail import send_mail
from django.conf import settings
from jobsapp.models import Notification


def create_notification(user, title, message, link=None):
    """
    Creates an in-app notification for the user.
    """
    if not user:
        return None
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        link=link
    )
    return notification


def send_event_email(user_email, subject, message):
    """
    Sends a transactional email notification safely using environment settings.
    """
    if not user_email:
        return False
    try:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@jobportal.com")
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[user_email],
            fail_silently=True,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
