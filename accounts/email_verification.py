"""
Email verification utilities for EthioJobPortal.
Sends a secure token link to the user's inbox on registration.
"""
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags


def send_verification_email(request, user):
    """
    Generate a new email token and send the verification link to the user.
    Expires in 24 hours.
    """
    # Refresh token each time (rotate for security)
    user.email_token = uuid.uuid4()
    user.email_token_expires = timezone.now() + timedelta(hours=24)
    user.is_active = False      # Deactivate until email confirmed
    user.email_verified = False
    user.save(update_fields=["email_token", "email_token_expires", "is_active", "email_verified"])

    # Build the verification URL
    scheme = "https" if not settings.DEBUG else "http"
    host = request.get_host()
    verify_url = f"{scheme}://{host}/verify-email/{user.email_token}/"

    subject = "✅ Verify your EthioJobPortal account"
    message = (
        f"Hello {user.first_name or user.email},\n\n"
        f"Thank you for registering on EthioJobPortal.\n\n"
        f"Please click the link below to verify your email address and activate your account:\n\n"
        f"{verify_url}\n\n"
        f"This link expires in 24 hours.\n\n"
        f"If you did not register on EthioJobPortal, please ignore this email.\n\n"
        f"— EthioJobPortal Team"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        # Log but don't crash registration
        import logging
        logging.getLogger(__name__).error(f"Failed to send verification email to {user.email}: {e}")
        return False
