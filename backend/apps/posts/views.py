from django.shortcuts import render
from rest_framework import viewsets, status,generics,permissions,parsers
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from .models import Post, Like, Comment
from .serializers import PostSerializer, LikeSerializer, CommentSerializer, PostCreateSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from apps.users.serializers import UserProfileSerializer
from rest_framework.views import APIView
from .feeds import FeedGenerator
from apps.users.permissions import IsOwnerOrReadOnly
from apps.connections.models import Connection

class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser, parsers.FormParser]



    def get_queryset(self):
        queryset = Post.objects.filter(is_published=True).select_related('author', 'author__profile'
                                                                         ).prefetch_related('likes', 'comments', 'likes__user', 'comments__user'
                                                                         ).order_by('-created_at')
        if self.action == 'list':
            user = self.request.user
            
            # Get user's connections
            user_connections = Connection.objects.filter(
                Q(from_user=user) | Q(to_user=user), 
                status='accepted'
            ).values_list('to_user_id', 'from_user_id')

            my_connections_ids = set()

            for to_user_id, from_user_id in user_connections:
                my_connections_ids.add(from_user_id)
                my_connections_ids.add(to_user_id)

            my_connections_ids.discard(user.user_id)
            
            # Filter posts based on visibility and connections
            queryset = queryset.filter(
                Q(visibility='public') |
                Q(visibility='connections', author_id__in=my_connections_ids) |
                Q(author=user)
            )    
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateSerializer
        elif self.action == 'comment':
            return CommentSerializer
        return PostSerializer
        
    def perform_create(self,serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'])
    def feed(self,request):
        """Get personalized feed for the user"""
        offset = int (request.query_params.get('offset', 0))
        limit = int (request.query_params.get('limit', 20))
        feed_posts = FeedGenerator.get_user_feed(request.user, offset, limit)
        serializer = self.get_serializer(feed_posts, many=True)
        return Response({'posts':serializer.data, 'count': len(feed_posts)}, status=status.HTTP_200_OK)
    

    @action(detail=True,methods=['post'],permission_classes=[IsAuthenticated])
    def like(self,request,pk=None):
        post = self.get_object()
        like,created = Like.objects.get_or_create(user=request.user, post=post)
        if created:
            post.like_count = F('like_count') + 1
            post.save()
            post.refresh_from_db()
            self._create_like_notification(request.user, post=post)     
        serializer = LikeSerializer(like)
        return Response(serializer.data,status=status.HTTP_200_OK)

    @action(detail=True,methods=['post'])
    def unlike(self,request,pk=None):
        post = self.get_object()
        deleted = Like.objects.filter(user=request.user, post=post).delete()
        if deleted[0]>0:
            post.like_ount = F('like_count') - 1
            post.save()
            post.refresh_from_db()

        return Response(status=status.HTTP_200_OK)
    
    @action(detail = True, methods=['get'])
    def comments(self,reqest, pk = None):
        post = self.get_object()
        comments = post.comments.filter(parent_comment__isnull=True).select_related('user').order_by('-created_at')
        comment_data =[{
            "name": comment.user.first_name,
            "comment": comment.content
        }
        for comment in comments
        ] 
        return Response(comment_data, status=status.HTTP_200_OK)
    

    @action(detail = True, methods= ['post'],permission_classes=[IsAuthenticated])
    def comment(self,request, pk = None):
        post = self.get_object()
        

        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            comment = serializer.save(user=request.user, post=post)
            
            post.comment_count = F('comment_count') + 1
            post.save()
            post.refresh_from_db()
            
            self._create_comment_notification(request.user, post, comment)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def _create_like_notification(self, user, post):
        from apps.notifications.models import Notification
        if user != post.author:
            Notification.objects.create(
                user=post.author,
                notification_type='post_like',
                actor=user,
                target_content_type='post',
                message=f"{user.first_name} liked your post"
            )

    def _create_comment_notification(self, user, post, comment):
        from apps.notifications.models import Notification
        if user != post.author:
            Notification.objects.create(
                user=post.author,
                notification_type='post_comment',
                actor=user,
                target_content_type='post',
                message=f"{user.first_name} commented on your post"
            )


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(
            post_id=self.kwargs['post_pk'],
            parent_comment__isnull=True
        ).select_related('user').prefetch_related('replies')

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        serializer.save(user=self.request.user, post=post)

    @action(detail=True, methods=['post'])
    def like(self, request, post_pk=None, pk=None):
        comment = self.get_object()
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reply(self, request, post_pk=None, pk=None):
        parent_comment = self.get_object()
        serializer = CommentSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            post = get_object_or_404(Post, pk=post_pk)
            reply = serializer.save(
                user=request.user, 
                post=post, 
                parent_comment=parent_comment
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)