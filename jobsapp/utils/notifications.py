import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import escape, linebreaks
from jobsapp.models import Notification

logger = logging.getLogger(__name__)


def create_notification(user, title, message, link=None):
    """
    Creates an in-app notification for the user.
    """
    if not user:
        return None
    try:
        clean_link = str(link) if link else None
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            link=clean_link,
            is_read=False,
        )
        logger.info(f"Created notification id={notification.id} for user={user.email}: '{title}'")
        return notification
    except Exception as e:
        logger.error(f"Failed to create notification for user={getattr(user, 'email', 'Unknown')}: {e}")
        return None


def send_event_email(user_email, subject, message, action_url=None, action_text=None):
    """
    Sends a styled transactional email notification safely.
    Supports both rich HTML and plain-text fallbacks.
    """
    if not user_email:
        return False

    try:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "Ethio Job Portal <noreply@ethiojobportal.com>")

        # Clean subject and message for Windows command prompt if using console backend
        backend_name = getattr(settings, "EMAIL_BACKEND", "")
        safe_subject = subject
        safe_message = message
        if "console" in backend_name.lower():
            safe_subject = subject.encode("ascii", errors="ignore").decode("ascii").strip() or subject
            safe_message = message.encode("ascii", errors="ignore").decode("ascii") or message

        button_html = ""
        if action_url and action_text:
            button_html = f"""
            <div style="margin: 28px 0; text-align: center;">
                <a href="{escape(action_url)}" style="background: #2563eb; color: #ffffff; padding: 12px 28px; font-size: 15px; font-weight: bold; text-decoration: none; border-radius: 6px; display: inline-block;">
                    {escape(action_text)}
                </a>
            </div>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px; color: #1e293b;">
            <div style="max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">
                <div style="background: linear-gradient(135deg, #0f172a, #1e3a8a); padding: 24px 30px; text-align: center;">
                    <h2 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: 700;">Ethio Job Portal</h2>
                    <p style="color: #93c5fd; margin: 6px 0 0 0; font-size: 13px;">Official Notification Alert</p>
                </div>
                <div style="padding: 30px 32px;">
                    <h3 style="margin-top: 0; color: #0f172a; font-size: 18px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px;">{escape(subject)}</h3>
                    <div style="font-size: 15px; line-height: 1.6; color: #334155;">
                        {linebreaks(escape(message))}
                    </div>
                    {button_html}
                    <div style="margin-top: 30px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b; text-align: center;">
                        <p style="margin: 0;">This is an automated system notification from Ethio Job Portal.</p>
                        <p style="margin: 4px 0 0 0;">Please do not reply directly to this email.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        msg = EmailMultiAlternatives(
            subject=safe_subject,
            body=safe_message,
            from_email=from_email,
            to=[user_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.encoding = "utf-8"
        msg.send(fail_silently=False)

        logger.info(f"Transactional email sent to {user_email}: '{subject}'")
        return True
    except Exception as e:
        logger.warning(f"Could not deliver email to {user_email} (check SMTP settings): {e}")
        return False
