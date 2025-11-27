import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.Logger(__name__)

resend.api_key = settings.RESEND_API_KEY

@shared_task
def send_email_verification(email, link):
    try:
        params = {
        "from": "NetCareer <onboarding@resend.dev>",
        "to": [email],
        "subject": "Email verification",
        "html": f'<p>Click to verify: <a href="{link}">{link}</a></p>'
        }
        
        resend.Emails.send(params)



        return f"Verification email sent to {email}"
    except Exception as e:
        logger.error(f"Error sending verification email to {email}: {e}")
        return f"Error sending verification email to {email}: {e}"
