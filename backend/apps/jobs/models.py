from django.db import models
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
import uuid


class Job(models.Model):

    JOB_TYPE_CHOICES = (
        ("full_time", "Full-time"),
        ("part_time", "Part-time"),
        ("contract", "Contract"),
        ("temporary", "Temporary"),
        ("volunteer", "Volunteer"),
        ("internship", "Internship"),
    )
    EXPERIENCE_LEVEL_CHOICES = (
        ("internship", "Internship"),
        ("entry", "Entry level"),
        ("associate", "Associate"),
        ("mid_senior", "Mid-Senior level"),
        ("director", "Director"),
        ("executive", "Executive"),
    )
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="jobs"
    )
    recruiter = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="jobs"
    )
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES)
    location = models.CharField(max_length=255)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2)
    is_remote = models.BooleanField(default=False)
    skills_required = models.TextField()
    is_active = models.BooleanField(default=True)
    search_vector = SearchVectorField(null=True)
    application_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of applications for this job",
    )
    salary_currency = models.CharField(max_length=3, default="USD")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "created_at"]),
            models.Index(fields=["job_type", "location"]),
            models.Index(fields=["company", "location"]),
            GinIndex(fields=["search_vector"]),
        ]


class JobApplication(models.Model):
    STATUS_CHOICES = (
        ("applied", "Applied"),
        ("reviewed", "Reviewed"),
        ("interview", "Interview"),
        ("rejected", "Rejected"),
        ("accepted", "Accepted"),
    )
    job_application_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="job_applications"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="applied")
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to="resumes/")

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["job", "applicant"]
