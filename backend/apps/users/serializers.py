from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserRegisterSerializer(serializers.ModelSerializer):
    """seroalizer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8, required=True)
    password_confirm = serializers.CharField(write_only=True, min_length=8, required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'role', 'password_confirm',
                   'admin_requested', 'is_verified', 'phone_number']
        read_only_fields = [ 'user_id','created_at', 'updated_at', 'is_active', 'is_verified']
    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm')
        if password != password_confirm:
            raise serializers.ValidationError('Passwords do not match')
        if attrs.get('role')=='admin':
            raise serializers.ValidationError('Admin role is reserved for superusers')
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return
class UserLoginSerializer(serializers.Serializer):
    """serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError('User not found')
        if not user.check_password(password):
            raise serializers.ValidationError('Incorrect password')
        if not user.is_verified:
            raise serializers.ValidationError('User not verified')
        attrs['user'] = user
        return attrs
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'email', 'first_name', 'last_name', 'role', 'admin_requested', 'is_verified', 'phone_number']
        read_only_fields = ['user_id', 'is_verified']

class EmailTokenObtainSerializer(serializers.Serializer):
    """Custom serializer to obtain Jwt token using email instead of username
    Returns access, refresh tokens and serialized user data
    """
    def validate(self, attrs):
        try:
            credentials = {
                'email': attrs.get('email'),
                'password': attrs.get('password')
            }
            user = authenticate(**credentials)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            refresh = RefreshToken.for_user(user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            }
            return data
        except Exception as e:
            raise serializers.ValidationError(str(e))
    