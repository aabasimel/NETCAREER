from django.db import models
import uuid
from django.conf import settings


class Notification(models.Model):
    notification_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    NOTIFICATION_TYPES = (
        ("connection_request", "Connection Request"),
        ("connection_accepted", "Connection Accepted"),
        ("post_like", "Post Like"),
        ("post_comment", "Post Comment"),
        ("job_recommendation", "Job Recommendation"),
        ("message", "Message"),
        ("profile_view", "Profile View"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    actor = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="acted_notifications"
    )
    target_content_type = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_read", "created_at"]),
        ]
        ordering = ["-created_at"]
