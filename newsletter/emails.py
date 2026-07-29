import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, html_body: str) -> None:
    """Send an email via Resend, or print it to the console if no API key is set.

    The console fallback lets the signup/send flows be exercised locally
    without a real Resend account.
    """
    if settings.RESEND_API_KEY:
        import resend

        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send(
            {
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html_body,
            }
        )
    else:
        logger.info("RESEND_API_KEY not set — sending %r to %s via console backend", subject, to_email)
        send_mail(
            subject=subject,
            message="This email requires an HTML-capable client.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_body,
        )
