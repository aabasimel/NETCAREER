"""
Reusable validators for serializers and models.
"""

import re
from django.core.exceptions import ValidationError


def validate_strong_password(value: str) -> None:
    """Basic strong password policy: 8+ length, upper, lower, digit."""
    if len(value) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", value):
        raise ValidationError("Password must include an uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValidationError("Password must include a lowercase letter")
    if not re.search(r"\d", value):
        raise ValidationError("Password must include a digit")
