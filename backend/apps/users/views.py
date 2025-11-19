from django.shortcuts import render
from rest_framework import viewsets,status,generics
from rest_framework.response import Response
from .models import User
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import EmailTokenObtainSerializer, UserRegisterSerializer, UserLoginSerializer, UserSerializer,VerifyEmailSerializer
from .utils import generate_email_token
from .tasks import send_email_verification
import jwt
from urllib.parse import unquote
from django.conf import settings
from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from .models import User
from .serializers import UserRegisterSerializer
from rest_framework.renderers import JSONRenderer

class UserRegistrationView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get('email')
        
        # Check if user already exists
        user = User.objects.filter(email=email).first()
        if user:
            if user.is_verified:
                return Response(
                    {'error': 'User with this email already exists and is verified'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # Resend verification email for unverified user
                token = generate_email_token(user)
                link = f"http://localhost:8000/verify-email/?token={token}"
                send_email_verification.delay(email, link)
                return Response(
                    {'message': 'Verification email sent to existing unverified user'}, 
                    status=status.HTTP_200_OK
                )
        
        # Create new user using serializer
        user = serializer.save()  
        
        # Send verification email
        token = generate_email_token(user)
        link = f"http://localhost:8000/verify-email/?token={token}"
        send_email_verification.delay(email, link)
        
        return Response(
            {
                'message': 'User registered successfully. Verification email sent.',
                'user_id': str(user.user_id),
                'email': user.email,
                'role': user.role
            },
            status=status.HTTP_201_CREATED
        )


class VerifyEmailView(APIView):
    serilaizer_class = VerifyEmailSerializer
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]
    def get(self, request):
        token = request.GET.get('token', '').strip()
        if not token:
            return Response({"error": "Token is required"}, status=400)

        token = unquote(token)

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')

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
# class UserLoginView(GenericAPIView):
#     serializer_class = UserLoginSerializer
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         email = serializer.validated_data['email']
#         password = serializer.validated_data['password']
        
#         # Authenticate user
#         user = authenticate(request, email=email, password=password)
        
#         if user is None:
#             # Try to find user and check password manually
#             try:
#                 user = User.objects.get(email=email)
#                 if not user.check_password(password):
#                     user = None
#             except User.DoesNotExist:
#                 user = None

#         if user is None:
#             return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
#         if not user.is_verified:
#             return Response({'error': 'User not verified'}, status=status.HTTP_401_UNAUTHORIZED)
        
#         refresh = RefreshToken.for_user(user)
#         access = refresh.access_token

#         return Response({
#             "access": str(access), 
#             "refresh": str(refresh),
#             "user": {
#                 "user_id": user.user_id,
#                 "email": user.email,
#                 "first_name": user.first_name,
#                 "last_name": user.last_name,
#                 "role": user.role
#             }
#         }, status=status.HTTP_200_OK)
class UserLoginView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = User.objects.filter(email=email).first()

        if user is None or not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=401)

        if not user.is_verified:
            return Response({"error": "Email not verified"}, status=403)

        # ✔ Generate REAL SimpleJWT tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response({
            "refresh": str(refresh),
            "access": str(access),
        }, status=200)