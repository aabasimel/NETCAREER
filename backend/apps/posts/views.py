from django.shortcuts import render
from rest_framework import viewsets, status,generics,permissions
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

class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]


    def get_queryset(self):
        queryset = Post.objects.filter(is_published=True).select_related('author', 'author__profile'
                                                                         ).prefetch_related('likes', 'comments', 'likes__user', 'comments__user'
                                                                         ).order_by('-created_at')
        if self.action == 'list':
            user = self.request.user
            queryset = queryset.filter(
                Q(visibility='public') |
                Q(visibility='public', author__in = user.connections.all())|
                Q(author=user)

            )     
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateSerializer
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
    

    @action(detail=True,methods=['post'])
    def like(self,request,pk=None):
        post = self.get_object()
        like,created = Liked.objects.get_or_create(user=request.user, post=post)
        if created:
            post.like_ount = F('like_count') + 1
            post.save()
            post.refresh_from_db()
            self._create_like_notification(request.user, request.user)     
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
        serializer= CommentSerializer(comments, many = True, context={'request': reqest})
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @action(detail = True, methods= ['post'])
    def comment(self,request, pk = None):
        post = self.get_object()
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            comment = serializer.save(user=request.user, post=post)
            
            # Update comment count
            post.comment_count = F('comment_count') + 1
            post.save()
            post.refresh_from_db()
            
            # Create notification
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