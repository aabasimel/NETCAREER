"""
Reusable DRF view mixins.
"""

from rest_framework.permissions import IsAuthenticated


class AuthenticatedMixin:
    """Ensure views require authentication by default."""

    permission_classes = [IsAuthenticated]
