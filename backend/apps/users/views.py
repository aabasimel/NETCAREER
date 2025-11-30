from urllib.parse import unquote

import jwt
from django.conf import settings
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend, OrderingFilter
from rest_framework import generics, status, viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .permissions import IsAdmin, IsEmployer, IsJobSeeker
from .serializers import (
    EmailTokenObtainSerializer,
    UpdateRoleSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)
from .tasks import send_email_verification
from .utils import generate_email_token
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.authtoken.models import Token
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from allauth.socialaccount.models import SocialAccount
from drf_spectacular.utils import extend_schema, OpenApiExample

# class UserRegistrationView(GenericAPIView):
#     permission_classes = [AllowAny]
#     serializer_class = UserRegistrationSerializer

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         email = serializer.validated_data.get("email")

#         # Check if user already exists
#         user = User.objects.filter(email=email).first()
#         if user:
#             if user.is_verified:
#                 return Response(
#                     {"error": "User with this email already exists and is verified"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )
#             else:
#                 # Resend verification email for unverified user
#                 token = generate_email_token(user)
#                 link = f"http://localhost:8080/auth/verify-email/?token={token}"
#                 send_email_verification.delay(email, link)
#                 return Response(
#                     {"message": "Verification email sent to existing unverified user"},
#                     status=status.HTTP_200_OK,
#                 )

#         # Create new user using serializer
#         user = serializer.save()

#         # Send verification email
#         token = generate_email_token(user)
#         link = f"http://localhost:8080/auth/verify-email/?token={token}"
#         send_email_verification.delay(email, link)

#         return Response(
#             {
#                 "message": "User registered successfully. Verification email sent.",
#                 "user_id": str(user.user_id),
#                 "email": user.email,
#                 "role": user.role,
#             },
#             status=status.HTTP_201_CREATED,
#         )



class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class VerifyEmailView(APIView):
    serilaizer_class = VerifyEmailSerializer
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]

    def get(self, request):
        token = request.GET.get("token", "").strip()
        if not token:
            return Response({"error": "Token is required"}, status=400)

        token = unquote(token)

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")

            user = User.objects.get(user_id=user_id)

            if user.is_verified:
                return Response({"message": "Account already verified"}, status=200)

            # Activate the user
            user.is_verified = True
            user.is_active = True
            user.save()

            return Response({"message": "Email verified successfully"}, status=200)

        except jwt.ExpiredSignatureError:
            return Response({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return Response({"error": "Invalid token"}, status=400)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)


class UserLoginView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = User.objects.filter(email=email).first()

        if user is None or not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=401)

        if not user.is_verified:
            return Response({"error": "Email not verified"}, status=403)

        # ✔ Generate REAL SimpleJWT tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response(
            {
                "refresh": str(refresh),
                "access": str(access),
            },
            status=200,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    try:
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model providing CRUD operations.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["role"]
    search_fields = ["first_name", "last_name", "email"]
    ordering_fields = ["first_name", "last_name", "created_at"]
    ordering = ["-created_at"]
    permission_classes = [IsAdmin]

    def get_serializer(self, *args, **kwargs):
        if self.action == "create":
            return UserRegistrationSerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)

    @action(detail=True, methods=["patch"], permission_classes=[IsAdmin])
    def change_role(self, request, pk=None):
        user = self.get_object()
        serlializer = UpdateRoleSerializer(
            user, data=request.data, partial=True, context={"request": request}
        )
        serlializer.is_valid(raise_exception=True)
        serlializer.save()
        return Response(serlializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def verify_user(self, request, pk=None):
        user = self.get_object()
        user.is_verified = True
        user.save()
        return Response(
            {"message": "User verified successfully"}, status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAdmin])
    def employers(self, request):
        employers = User.objects.filter(role="employer")
        serializer = UserSerializer(employers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], permission_classes=[IsAdmin])
    def jobseekers(self, request):
        jobseekers = User.objects.filter(role="jobseeker")
        serializer = UserSerializer(jobseekers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            tokens = OutstandingToken.objects.filter(user=request.user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
            return Response(
                {"message": "Logged out from all devices. All tokens invalidated."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
