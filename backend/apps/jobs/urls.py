from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import JobApplicationViewSet, JobViewSet

router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="jobs")
router.register(r"applications", JobApplicationViewSet, basename="job-applications")

urlpatterns = [
    path("", include(router.urls)),
]
