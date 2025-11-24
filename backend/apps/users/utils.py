from datetime import datetime, timedelta

import jwt
from django.conf import settings


def generate_email_token(user):
    payload = {
        "user_id": str(user.user_id),
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(days=1),
        "type": "email_confirmation",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
