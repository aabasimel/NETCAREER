# backend/apps/posts/urls.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from .views import CommentViewSet, PostViewSet

# Main router for posts
router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='posts')

# Nested router for comments under a specific post
posts_router = NestedDefaultRouter(router, r'posts', lookup='post')
posts_router.register(r'comments', CommentViewSet, basename='post-comments')

urlpatterns = [
    path('', include(router.urls)),         # /posts/ and /posts/<id>/ actions
    path('', include(posts_router.urls)),   # /posts/<post_pk>/comments/ and nested actions
]