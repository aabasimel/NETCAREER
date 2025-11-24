from rest_framework import serializers
from .models import Company 
from apps.users.serializers import UserProfileSerializer

class CompanySerializer(serializers.ModelSerializer):
    owner =UserProfileSerializer(read_only=True)
    is_owner = serializers.SerializerMethodField()
    logo = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)
    cover_image = serializers.ImageField(required=False, allow_null=True, allow_empty_file=True)
    website = serializers.URLField(required=True)
    
    class Meta:
        model = Company
        fields=(
            'company_id', 'name', 'description', 'website', 'logo', 'cover_image',
            'industry', 'company_size', 'founded_year', 'headquarters',
            'specialities', 'owner', 'is_owner',
            'created_at', 'updated_at'
        )
        read_only_fields = ('company_id', 'owner',  'created_at', 'updated_at')

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request and request.user == obj.owner
    
  
    
class CompanyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = (
            'name', 'description', 'website', 'logo', 'cover_image',
            'industry', 'company_size', 'founded_year', 'headquarters',
            'specialities'
        )
    def create(self,validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class CompanyStatsSerializer(serializers.ModelSerializer):
    job_count= serializers.SerializerMethodField()
    total_applications = serializers.SerializerMethodField()

    class Meta:
        model = Company 
        fields = ('company_id','name','follower_count','job_count', 'total_applications')
        
    def get_job_count(self,obj):
        return obj.jobs.filter(is_active=True).count()
    
    def get_total_applications(self, obj):
        from apps.jobs.models import JobApplication
        return JobApplication.objects.filter(job__company=obj).count()
    
class CompanyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = (
            'name', 'description', 'website', 'logo', 'cover_image',
            'industry', 'company_size', 'founded_year', 'headquarters',
            'specialities'
        )