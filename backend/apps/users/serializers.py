from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth.password_validation import validate_password
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, min_length=8, required=True, validators=[validate_password]
    )
    password_confirm = serializers.CharField(
        write_only=True, min_length=8, required=True
    )
    company_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "user_id",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "role",
            "admin_requested",
            "is_verified",
            "phone_number",
            "company_name",
        ]
        read_only_fields = ["user_id", "created_at", "updated_at", "is_verified"]
        extra_kwargs = {
            "email": {"validators": []}  # Disable automatic unique validation
        }

    def validate_email(self, value):
        """
        Custom email validation that allows unverified users to re-register
        """
        value = value.lower().strip()

        # Check if a verified user already exists with this email
        existing_user = User.objects.filter(email=value).first()
        if existing_user and existing_user.is_verified:
            raise serializers.ValidationError(
                "User with this email already exists and is verified."
            )

        return value

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match"}
            )

        role = attrs.get("role")
        if role == "admin":
            raise serializers.ValidationError(
                {"role": "Admin role is reserved for superusers"}
            )

        if role == "employer":
            company_name = attrs.get("company_name")
            if not company_name:
                raise serializers.ValidationError(
                    {"company_name": "Company name is required for employers"}
                )

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        company_name = validated_data.pop("company_name", None)

        password = validated_data.pop("password")

        # Check if unverified user already exists
        email = validated_data["email"]
        existing_user = User.objects.filter(email=email, is_verified=False).first()

        if existing_user:
            # Update the existing unverified user
            for attr, value in validated_data.items():
                setattr(existing_user, attr, value)
            existing_user.set_password(password)
            existing_user.save()
            return existing_user

        # Create new user
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user


class UserLoginSerializer(serializers.Serializer):
    """serializer for user login"""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError("User not found")
        if not user.check_password(password):
            raise serializers.ValidationError("Incorrect password")
        if not user.is_verified:
            raise serializers.ValidationError("User not verified")
        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "user_id",
            "email",
            "first_name",
            "last_name",
            "role",
            "admin_requested",
            "is_verified",
            "phone_number",
        ]
        read_only_fields = ["user_id", "is_verified", "phone_number"]


class EmailTokenObtainSerializer(serializers.Serializer):
    """Custom serializer to obtain Jwt token using email instead of username"""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            credentials = {
                "username": attrs.get("email"),
                "password": attrs.get("password"),
            }
            user = authenticate(**credentials)
            if not user:
                raise serializers.ValidationError("Invalid credentials")

            if not user.is_verified:
                raise serializers.ValidationError("User not verified")

            refresh = RefreshToken.for_user(user)
            data = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            }
            return data
        except Exception as e:
            raise serializers.ValidationError(str(e))


class VerifyEmailSerializer(serializers.Serializer):
    """Empty serializer for VerifyEmailView - just to satisfy DRF schema generation"""

    pass


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "user_id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "user",
        )


class UpdateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("role",)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.is_admin():
            raise serializers.ValidationError("Only admin users can update role")
        return attrs
