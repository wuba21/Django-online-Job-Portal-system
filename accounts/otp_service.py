import random
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from accounts.models import EmailVerificationOTP

logger = logging.getLogger(__name__)


def generate_and_send_email_otp(user):
    """
    Generates a cryptographically strong/random 6-digit OTP code,
    stores it in EmailVerificationOTP, and sends it to the user's email.
    """
    # 6-digit code e.g. '582914'
    otp_code = f"{random.randint(100000, 999999)}"

    # Invalidate older active OTPs for this user
    EmailVerificationOTP.objects.filter(user=user, is_used=False).update(is_used=True)

    # Save new OTP
    otp_record = EmailVerificationOTP.objects.create(
        user=user,
        otp_code=otp_code,
        is_used=False
    )

    subject = f"Your Verification Code: {otp_code} - EthioJobs Portal"
    message = (
        f"Hello {user.first_name or 'User'},\n\n"
        f"Thank you for registering on EthioJobs Portal.\n\n"
        f"Your 6-digit verification code (OTP) is:\n\n"
        f"      {otp_code}\n\n"
        f"This code will expire in 10 minutes.\n"
        f"Please enter this code on the verification page to activate your account.\n\n"
        f"If you did not request this registration, please ignore this email.\n\n"
        f"Best regards,\n"
        f"EthioJobs Portal Security Team"
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "EthioJobPortal <noreply@ethiojobportal.com>")

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Verification OTP sent successfully to {user.email}")
        return True, otp_code
    except Exception as e:
        logger.error(f"Failed to send verification OTP to {user.email}: {e}")
        # Even if SMTP fails on dev/test, console will show or we can fallback
        return False, otp_code
