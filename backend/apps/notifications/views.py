from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Notification
from .serializers import (
    NotificationSerializer, NotificationUpdateSerializer,
    NotificationCountSerializer, NotificationPreferencesSerializer
)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).select_related('actor', 'actor__profile').order_by('-created_at')

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'mark_read']:
            return NotificationUpdateSerializer
        return NotificationSerializer

    def list(self, request, *args, **kwargs):
        """Get notifications with pagination and filtering"""
        queryset = self.filter_queryset(self.get_queryset())
        
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            if is_read.lower() == 'true':
                queryset = queryset.filter(is_read=True)
            elif is_read.lower() == 'false':
                queryset = queryset.filter(is_read=False)
        
        notification_type = request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def count(self, request):
        """Get notification counts"""
        total_count = self.get_queryset().count()
        unread_count = self.get_queryset().filter(is_read=False).count()
        
        serializer = NotificationCountSerializer({
            'unread_count': unread_count,
            'total_count': total_count
        })
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        serializer = self.get_serializer(notification, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        
        return Response({
            'status': f'Marked {updated} notifications as read',
            'updated_count': updated
        })

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent notifications (last 7 days)"""
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_notifications = self.get_queryset().filter(
            created_at__gte=seven_days_ago
        )[:10]  
        
        serializer = self.get_serializer(recent_notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'put'])
    def preferences(self, request):
        """Get or update notification preferences"""
        if request.method == 'GET':
            default_preferences = {
                'email_notifications': True,
                'push_notifications': True,
                'connection_requests': True,
                'connection_accepted': True,
                'post_interactions': True,
                'job_alerts': True,
                'message_notifications': True,
                'profile_views': True,
                'company_updates': True,
            }
            serializer = NotificationPreferencesSerializer(default_preferences)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            serializer = NotificationPreferencesSerializer(data=request.data)
            if serializer.is_valid():
                # In a real app, save these to user settings
                # For now, just return the validated data
                return Response(serializer.validated_data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Delete all notifications"""
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        deleted_count, _ = self.get_queryset().delete()
        
        return Response({
            'status': f'Deleted {deleted_count} notifications',
            'deleted_count': deleted_count
        })

    @action(detail=False, methods=['delete'])
    def clear_read(self, request):
        """Delete all read notifications"""
        deleted_count, _ = self.get_queryset().filter(is_read=True).delete()
        
        return Response({
            'status': f'Deleted {deleted_count} read notifications',
            'deleted_count': deleted_count
        })

class NotificationWebhookViewSet(viewsets.ViewSet):
    """Webhook for real-time notifications (would integrate with WebSockets)"""
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        """Subscribe to real-time notifications"""
        
        return Response({
            'status': 'Subscribed to real-time notifications',
            'channel': f'user_{request.user.id}_notifications'
        })

    @action(detail=False, methods=['post'])
    def unsubscribe(self, request):
        """Unsubscribe from real-time notifications"""
        return Response({
            'status': 'Unsubscribed from real-time notifications'
        })