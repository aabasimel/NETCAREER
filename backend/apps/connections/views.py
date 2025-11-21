from rest_framework import status,viewsets, permissions
from .models import Connection, Follow
from rest_framework.decorators import api_view, permission_classes,action
from rest_framework.response import Response
from django.db.models import Q, F
from .serializers import ConnectionSerializer, FollowSerializer,ConnectionCreateSerializer

from apps.users.models import User
from apps.notifications.models import Notification
from apps.profiles.models import Profile
from apps.users.serializers import UserProfileSerializer
from apps.profiles.models import Profile


class ConnectionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Connection.objects.filter(Q(from_user=self.request.user)| Q(to_user=self.request.user)
                                         ).select_related('from_user', 'to_user')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConnectionCreateSerializer
        return ConnectionSerializer

    def perform_create(self,serializer):
        connection = serializer.save()
        Notification.objects.create(
            user = connection.to_user,
            notification_type = 'connection_request',
            actor = connection.from_user,
            target_content_type = 'connection',
            message = f"{connection.from_user.first_name} wants to connect with you"

        )
    @action(detail=False, methods = ['get'])
    def pending(self, request):
        """Get pending connection requests"""
        pending_connections = Connection.objects.filter(to_user=request.user, status='pending')
        serializer = ConnectionSerializer(pending_connections, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods = ['get'])
    def accepted(self, request):
        """Get accepted connections"""
        accepted_connections = Connection.objects.filter(to_user=request.user, status='accepted')
        serializer = ConnectionSerializer(accepted_connections, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods = ['get'])
    def rejected(self, request):
        """Get rejected connections"""
        rejected_connections = Connection.objects.filter(to_user=request.user, status='rejected')
        serializer = ConnectionSerializer(rejected_connections, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods = ['post'])
    def accept(self,request,pk=None):
        """Accept a connecton request"""
        connection = self.get_object()

        if connection.to_user != request.user:
            return Response({"message": "You are not authorized to accept this connection"}, status=status.HTTP_403_FORBIDDEN)
        connection.status = 'accepted'
        connection.save()
    # Update connection counts for both users
        Profile.objects.filter(user=connection.from_user).update(connection_count=F('connection_count') + 1)
        Profile.objects.filter(user=connection.to_user).update(connection_count=F('connection_count') + 1)

        Notification.objects.create(
            user = connection.from_user,
            notification_type = 'connection_accept',
            actor = connection.to_user,
            target_content_type = 'connection',
            message = f"{connection.to_user.first_name} accepted your connection request"
        )
        return Response({"message": "Connection accepted"}, status=status.HTTP_200_OK)

    @action(detail=True, methods = ['post'])
    def reject(self,request,pk=None):
        """Reject a connecton request"""
        connection = self.get_object()

        if connection.to_user != request.user:
            return Response({"message": "You are not authorized to reject this connection"}, status=status.HTTP_403_FORBIDDEN)
        connection.status = 'rejected'
        connection.save()
        Notification.objects.create(
            user = connection.from_user,
            notification_type = 'connection_reject',
            actor = connection.to_user,
            target_content_type = 'connection',
            message = f"{connection.to_user.first_name} rejected your connection request"
        )
        return Response({"message": "Connection rejected"}, status=status.HTTP_200_OK)
    @action(detail=False, methods=['get'])
    def suggestions(self, request):
        try:

            user_connections = Connection.objects.filter(
                Q(from_user=request.user) | Q(to_user=request.user), 
                status='accepted'
            ).values_list('to_user_id', 'from_user_id')

            my_connections_ids = set()

            for to_user_id, from_user_id in user_connections:
                my_connections_ids.add(from_user_id)
                my_connections_ids.add(to_user_id)

            my_connections_ids.discard(request.user.user_id) 

            if my_connections_ids:
                connections_my_connections = Connection.objects.filter(
                    Q(from_user_id__in=my_connections_ids) | Q(to_user_id__in=my_connections_ids), 
                    status='accepted'
                ).values_list('to_user_id', 'from_user_id')

                connections_my_connections_ids = set()

                for to_user_id, from_user_id in connections_my_connections:
                    connections_my_connections_ids.add(from_user_id)
                    connections_my_connections_ids.add(to_user_id)

                connections_my_connections_ids.discard(request.user.user_id)
                connections_my_connections_ids -= my_connections_ids

                suggested_connections = User.objects.filter(
                    user_id__in=connections_my_connections_ids,
                ).exclude(
                    user_id__in=my_connections_ids
                ).exclude(
                    user_id=request.user.user_id
                )[:20]

                serializer = UserProfileSerializer(suggested_connections, many=True,context={'request':request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response([], status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in suggestions: {e}")
            return Response(
                {'error': 'Unable to fetch suggestions'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer

    def get_queryset(self):
        user = self.request.user
        return Follow.objects.filter(follower=user)
    def perform_create(self, serializer):
        following = serializer.validated_data['following']

        if self.request.user == following:
            raise serializer.ValidationError({'following': 'You cannot follow yourself'})

        if Follow.objects.filter(follower=self.request.user, following=following).exists():
            raise serializer.ValidationError({'following': 'You are already following this user'})
        serializer.save(follower=self.request.user)

    @action(detail=False, methods = ['get'])
    def followers(self,request):
        followers = Follow.objects.filter(following=request.user).select_related('follower')
        serializer = FollowSerializer(followers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods = ['get'])
    def following(self,request):
        following = Follow.objects.filter(follower=request.user).select_related('following')
        serializer = FollowSerializer(following, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)






