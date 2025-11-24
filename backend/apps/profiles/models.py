from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
import uuid


class Profile(models.Model):
    profile_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="profile",
        to_field="user_id",
    )
    headline = models.CharField(max_length=255, blank=True)
    about = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    cover_image = models.ImageField(upload_to="covers/", blank=True)

    search_vector = SearchVectorField(null=True)

    profile_views = models.IntegerField(default=0)
    connection_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            GinIndex(fields=["search_vector"]),
            models.Index(fields=["location"]),
        ]


class Experience(models.Model):
    EMPLOYMENT_TYPE_CHOICES = (
        ("full_time", "Full-time"),
        ("part_time", "Part-time"),
        ("contract", "Contract"),
        ("freelance", "Freelance"),
        ("internship", "Internship"),
    )
    experience_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="experiences"
    )
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES)
    location = models.CharField(max_length=255, blank=True)
    currently_working = models.BooleanField(default=False)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)


class Education(models.Model):
    education_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="educations"
    )
    school = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    grade = models.CharField(max_length=50, blank=True)
    activities = models.TextField(blank=True)
