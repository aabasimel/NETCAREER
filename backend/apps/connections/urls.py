from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConnectionViewSet, FollowViewSet

router = DefaultRouter()

router.register(r"connections", ConnectionViewSet, basename="connections")
router.register(r"follows", FollowViewSet, basename="follows")

urlpatterns = [
    path("", include(router.urls)),
]
