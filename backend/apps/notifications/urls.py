from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'webhooks', views.NotificationWebhookViewSet, basename='webhook')

urlpatterns = [
    path('', include(router.urls)),
]