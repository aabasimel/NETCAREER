from apps.users.serializers import UserProfileSerializer
from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor = UserProfileSerializer(read_only=True)
    target_url = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            "notification_id",
            "notification_type",
            "actor",
            "message",
            "target_content_type",
            "target_url",
            "is_read",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def get_target_url(self, obj):
        """Generate frontend URL based on notification type"""
        notification_urls = {
            "connection_request": f"/connections/{obj.actor.user_id}",
            "connection_accepted": f"/connections/{obj.actor.user_id}",
            "post_like": f"/profile/{obj.actor.user_id}",
            "post_comment": f"/profile/{obj.actor.user_id}",
            "job_recommendation": "/jobs",
            "message": f"/messages/{obj.actor.user_id}",
            "profile_view": f"/profile/{obj.actor.user_id}",
        }
        return notification_urls.get(obj.notification_type, "#")


class NotificationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("is_read",)


class NotificationCountSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()
    total_count = serializers.IntegerField()


class NotificationPreferencesSerializer(serializers.Serializer):
    email_notifications = serializers.BooleanField(default=True)
    push_notifications = serializers.BooleanField(default=True)
    connection_requests = serializers.BooleanField(default=True)
    connection_accepted = serializers.BooleanField(default=True)
    post_interactions = serializers.BooleanField(default=True)
    job_alerts = serializers.BooleanField(default=True)
    message_notifications = serializers.BooleanField(default=True)
    profile_views = serializers.BooleanField(default=True)
    company_updates = serializers.BooleanField(default=True)
