
from rest_framework import serializers
from .models import Profile, Education, Experience
from apps.users.serializers import UserProfileSerializer

class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model=Experience
        fields='__all__'
        read_only_fields = ['profile','created_at', 'updated_at','experience_id'] 

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("Start date must be before end date")
        return data

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model=Education
        fields='__all__'
        read_only_fields = ['profile','created_at', 'updated_at','education_id']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    class Meta:
        model=Profile
        fields=('profile_id','user','full_name','headline','about','location','website',
                'avatar','cover_image','educations','experiences','profile_views','connection_count',
                'created_at', 'updated_at')
        read_only_fields = ['profile_id','user','created_at', 'updated_at','profile_views','connection_count','search_vector']

class ProfileUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)

    class Meta:
        model = Profile
        fields = ('headline', 'about', 'location', 'website', 'avatar', 
                 'cover_image', 'first_name', 'last_name')
        
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.save()
        return super().update(instance, validated_data)


class ProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating profile data"""
    educations = EducationSerializer(many=True, required=False)
    experiences = ExperienceSerializer(many=True, required=False)

    class Meta:
        model = Profile
        fields = ('headline', 'about', 'location', 'website', 'avatar', 'cover_image', 
                 'educations', 'experiences')

    def create(self, validated_data):
        educations_data = validated_data.pop('educations', [])
        experiences_data = validated_data.pop('experiences', [])
        
        profile = Profile.objects.create(**validated_data)
        
        for education_data in educations_data:
            Education.objects.create(profile=profile, **education_data)
        
        for experience_data in experiences_data:
            Experience.objects.create(profile=profile, **experience_data)
        
        return profile

    def update(self, instance, validated_data):
        educations_data = validated_data.pop('educations', None)
        experiences_data = validated_data.pop('experiences', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if educations_data is not None:
            instance.educations.all().delete()  
            for education_data in educations_data:
                Education.objects.create(profile=instance, **education_data)
        
        if experiences_data is not None:
            instance.experiences.all().delete()  
            for experience_data in experiences_data:
                Experience.objects.create(profile=instance, **experience_data)
        
        return instance