from rest_framework import serializers
from .models import Connection, Follow
from apps.users.serializers import UserProfileSerializer

class ConnectionSerializer(serializers.ModelSerializer):
    from_user = UserProfileSerializer()
    to_user = UserProfileSerializer()
    can_accept = serializers.SerializerMethodField()
    class Meta:
        model = Connection
        fields = ('connection_id', 'from_user', 'to_user', 'status', 'can_accept', 'message', 'created_at', 'updated_at')
        read_only_fields = ['connection_id', 'from_user', 'created_at', 'updated_at']

    def get_can_accept(self, obj):
        request = self.context.get('request')
        return request and request.user == obj.to_user
    

class ConnectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = ( 'to_user','message')
    def validate(self, attrs):
        request = self.context.get('request')
        to_user = attrs.get('to_user')

        if request.user == to_user:
            raise serializers.ValidationError('You cannot connect with yourself')
        if Connection.objects.filter(from_user=request.user, to_user=to_user).exists():
            raise serializers.ValidationError('Connection already exists')
        if Connection.objects.filter(from_user=to_user, to_user=request.user).exists():
            raise serializers.ValidationError('Connection already exists')
        return attrs
    
    def create(self, validated_data):
        request = self.context.get('request')
        to_user = validated_data.pop('to_user')
        connection = Connection.objects.create(from_user=request.user, to_user=to_user, **validated_data)
        return connection


class FollowSerializer(serializers.ModelSerializer):
    follower = UserProfileSerializer()
    following = UserProfileSerializer()
    class Meta:
        model = Follow
        fields = ('follower_id','follower', 'following', 'created_at')
        read_only_fields = ['follower_id','created_at']