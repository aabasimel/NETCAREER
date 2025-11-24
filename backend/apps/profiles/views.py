from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, F
from .models import Profile
from .serializers import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    EducationSerializer,
    ExperienceSerializer,
)
from .models import Education, Experience, Profile
from rest_framework.pagination import PageNumberPagination
from apps.users.permissions import IsOwnerOrReadOnly
from rest_framework import serializers


class ProfileDetailView(generics.RetrieveAPIView):
    queryset = Profile.objects.select_related("user").prefetch_related(
        "educations", "experiences"
    )
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            Profile.objects.filter(pk=instance.pk).update(
                profile_views=F("profile_views") + 1
            )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            profile, created = Profile.objects.get_or_create(user=self.request.user)
            return profile
        except Profile.DoesNotExist:
            return Profile.objects.create(user=self.request.user)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})

    def get_serializer(self, *args, **kwargs):
        if self.request.method in ["PATCH", "PUT"]:
            return ProfileUpdateSerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)


class ExperienceListCreateView(generics.ListCreateAPIView):
    serializer_class = ExperienceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Experience.objects.filter(profile=self.request.user.profile)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class ExperienceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExperienceSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Experience.objects.filter(profile=self.request.user.profile)

    def perform_update(self, serializer):
        serializer.save(profile=self.request.user.profile)


class EducationListCreateView(generics.ListCreateAPIView):
    serializer_class = EducationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Education.objects.filter(profile=self.request.user.profile)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)


class EducationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EducationSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Education.objects.filter(profile=self.request.user.profile)

    def perform_update(self, serializer):
        serializer.save(profile=self.request.user.profile)
