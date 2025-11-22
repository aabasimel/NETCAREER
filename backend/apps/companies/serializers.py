from rest_framework import serializers
from .models import Company 
from apps.users.serializers import UserProfileSerializer

class CompanySerializer(serializers.ModelSerializer):
    owner =UserProfileSerializer(read_only=True)
    is_owner = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    class Meta:
        model = Company
        fields=(
            'company_id', 'name', 'description', 'website', 'logo', 'cover_image',
            'industry', 'company_size', 'founded_year', 'headquarters',
            'specialities', 'follower_count', 'owner', 'is_owner',
            'is_following',  'created_at', 'updated_at'
        )
        read_only_fields = ('company_id', 'owner', 'follower_count', 'created_at', 'updated_at')

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return request.user == obj.owner
    
        
        