import uuid
from decimal import Decimal

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone as datimezone


class CustomUserManager(BaseUserManager):
    """Custom manager for User model using email instead of username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):

    ROLE_CHOICES = [
        ("jobseeker", "Jobseeker"),
        ("employer", "Employer"),
        ("admin", "Admin"),
    ]

    user_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="jobseeker")
    admin_requested = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)

    is_superuser = models.BooleanField(default=False)

    username = None
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        db_table = "user"
        indexes = [
            models.Index(fields=["email"], name="idx_user_email"),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def is_jobseeker(self):
        return self.role == "jobseeker"

    def is_employer(self):
        return self.role == "employer"

    def is_admin(self):
        return self.role == "admin"
