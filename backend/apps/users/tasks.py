from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging
logger = logging.Logger(__name__)

@shared_task
def send_email_verification(email,link):
    try:
        subject = "Email verification"
        message = f"Please click on the link to verify your email: {link}"

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,

        )
        return f"Verification email sent to {email}"
    except Exception as e:
        logger.error(f"Error sending verification email to {email}: {e}")
        return f"Error sending verification email to {email}: {e}"

       
       
