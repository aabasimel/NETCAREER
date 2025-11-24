from rest_framework import serializers
from .models import Job, JobApplication
from apps.users.serializers import UserProfileSerializer
from apps.companies.serializers import CompanySerializer
from apps.companies.models import Company


class JobSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    recruiter = UserProfileSerializer(read_only=True)
    has_applied = serializers.SerializerMethodField()
    application_count = serializers.ReadOnlyField()

    class Meta:
        model = Job
        fields = (
            "job_id",
            "title",
            "description",
            "company",
            "recruiter",
            "job_type",
            "experience_level",
            "location",
            "is_remote",
            "salary_min",
            "salary_max",
            "salary_currency",
            "skills_required",
            "is_active",
            "has_applied",
            "application_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "job_id",
            "recruiter",
            "application_count",
            "created_at",
            "updated_at",
        )

    def get_has_applied(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return JobApplication.objects.filter(
                job=obj, applicant=request.user
            ).exists()
        return False


class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = (
            "title",
            "description",
            "company",
            "recruiter",
            "job_type",
            "experience_level",
            "location",
            "is_remote",
            "salary_min",
            "salary_max",
            "salary_currency",
            "skills_required",
        )

    def validate(self, data):
        """Validate the entire data set"""
        # Check if salary_min is less than salary_max
        salary_min = data.get("salary_min")
        salary_max = data.get("salary_max")

        if salary_min and salary_max and salary_min > salary_max:
            raise serializers.ValidationError(
                {"salary_max": "Maximum salary must be greater than minimum salary"}
            )

        return data

    def create(self, validated_data):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required")

        validated_data["recruiter"] = request.user

        if hasattr(request.user, "company"):
            validated_data["company"] = request.user.company
        elif hasattr(request.user, "companies") and request.user.companies.exists():
            validated_data["company"] = request.user.companies.first()
        else:
            raise serializers.ValidationError(
                "User must be associated with a company to create jobs"
            )

        return super().create(validated_data)


class JobApplicationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    applicant = UserProfileSerializer(read_only=True)

    class Meta:
        model = JobApplication
        fields = (
            "job_application_id",
            "job",
            "applicant",
            "cover_letter",
            "resume",
            "status",
            "updated_at",
        )
        read_only_fields = ("job_application_id", "job", "applicant", "updated_at")


class JobApplicationCreateSerializer(serializers.ModelSerializer):
    company = serializers.UUIDField(write_only=True)  # Remove the source parameter

    class Meta:
        model = JobApplication
        fields = ("cover_letter", "resume", "job", "company")
        extra_kwargs = {
            "cover_letter": {"required": False, "allow_blank": True},
            "resume": {"required": True},
            "job": {"required": True},
        }

    def validate_company(self, value):
        """Convert UUID to Company object"""
        try:
            return Company.objects.get(company_id=value)
        except Company.DoesNotExist:
            raise serializers.ValidationError("Company not found")

    def validate(self, data):
        request = self.context.get("request")
        job = data.get("job")
        company = data.get("company")  # This is now a Company object

        # Check if user already applied for this job
        if JobApplication.objects.filter(job=job, applicant=request.user).exists():
            raise serializers.ValidationError(
                {"detail": "You have already applied for this job"}
            )

        # Validate that the job belongs to the specified company
        if job.company != company:
            raise serializers.ValidationError(
                {"company": "This job does not belong to the specified company"}
            )

        # Check if job is active
        if not job.is_active:
            raise serializers.ValidationError(
                {"job": "This job is no longer accepting applications"}
            )

        return data

    def create(self, validated_data):
        request = self.context.get("request")

        # Remove company from validated_data since it's not a field in JobApplication
        validated_data.pop("company", None)

        application = JobApplication.objects.create(
            applicant=request.user, **validated_data
        )

        # Update application count on the job
        application.job.application_count += 1
        application.job.save()

        return application


class JobApplicationApplySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ("cover_letter", "resume")
        extra_kwargs = {
            "cover_letter": {"required": False, "allow_blank": True},
            "resume": {"required": True},
        }

    def create(self, validated_data):
        job = self.context.get("job")
        applicant = self.context["request"].user

        if not job:
            raise serializers.ValidationError("Job is required")

        application = JobApplication.objects.create(
            job=job, applicant=applicant, **validated_data
        )
        return application
