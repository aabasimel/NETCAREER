# profiles/urls.py
from django.urls import path

from .views import (
    EducationDetailView,
    EducationListCreateView,
    ExperienceDetailView,
    ExperienceListCreateView,
    MyProfileView,
    ProfileDetailView,
)

app_name = "profiles"

urlpatterns = [
    # Profile endpoints
    path("profiles/me/", MyProfileView.as_view(), name="my-profile"),
    path("profiles/<uuid:pk>/", ProfileDetailView.as_view(), name="profile-detail"),
    # My profile's experiences
    path(
        "profiles/me/experiences/",
        ExperienceListCreateView.as_view(),
        name="my-experience-list",
    ),
    path(
        "profiles/me/experiences/<uuid:pk>/",
        ExperienceDetailView.as_view(),
        name="my-experience-detail",
    ),
    # My profile's educations
    path(
        "profiles/me/educations/",
        EducationListCreateView.as_view(),
        name="my-education-list",
    ),
    path(
        "profiles/me/educations/<uuid:pk>/",
        EducationDetailView.as_view(),
        name="my-education-detail",
    ),
    # Other users' profile experiences/educations (read-only)
    path(
        "profiles/<uuid:profile_pk>/experiences/",
        ExperienceListCreateView.as_view(),
        name="profile-experience-list",
    ),
    path(
        "profiles/<uuid:profile_pk>/educations/",
        EducationListCreateView.as_view(),
        name="profile-education-list",
    ),
]
