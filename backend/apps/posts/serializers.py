from rest_framework import serializers
from .models import Post, Like, Comment
from apps.users.serializers import UserProfileSerializer

class CommentSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    class Meta:
        model = Comment
        fields = 'comment_id', 'user', 'post', 'parent_comment', 'content', 'like_count','replies','can_edit', 'created_at', 'updated_at'
    
    def get_replies(self, obj):
        # Check if the replies have already been prefetched
        if hasattr(obj, 'replies_prefetched'):
            replies = obj.replies_prefetched
        else:
            replies = obj.replies.all()
        
        return CommentSerializer(replies, many=True).data

    def get_can_edit(self, obj):
        request = obj.user == self.context['request']
        return request and request.user == obj.user
    
     
class LikeSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    class Meta:
        model = Like
        fields = 'like_id', 'user', 'post'
        read_only_fields = ['like_id', 'user', 'post']

class PostSerializer(serializers.ModelSerializer):

    author = UserProfileSerializer(read_only=True)
    likes = LikeSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    has_liked = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    comment_count = serializers.ReadOnlyField()

    class Meta: 
        model = Post
        fields = ('post_id', 'author', 'content_type', 'content', 'image', 'video', 
                 'link', 'link_preview', 'visibility', 'is_published', 
                 'like_count', 'comment_count', 'share_count', 'likes', 'comments',
                 'has_liked', 'can_edit', 'created_at', 'updated_at')
        read_only_fields = ('post_id', 'author', 'like_count', 'comment_count', 
                          'share_count', 'created_at', 'updated_at')
        
    def get_hast_liked(self,obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter( user=request.user).exists()
        return False
    def get_can_edit(self, obj):
        request = self.context.get('request')
        return request and request.user == obj.author
    
    def validate(self, attrs):
        content_type = attrs.get('content_type')
        if content_type == 'image' and not attrs.get('image'):
            raise serializers.ValidationError("Image is required for image posts")
        
        if content_type == 'video' and not attrs.get('video'):
            raise serializers.ValidationError("Video is required for video posts")
        
        return attrs


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('content_type', 'content', 'image', 'video', 'link', 'visibility')
        extra_kwargs = {
            'image': {'required': False, 'allow_null': True},
            'video': {'required': False, 'allow_null': True},
            'link': {'required': False, 'allow_null': True},
        }
    def create(self, validated_data):
        if validated_data.get('image') == '':
            validated_data['image'] = None
        if validated_data.get('video') == '':
            validated_data['video'] = None
        if validated_data.get('link') == '':
            validated_data['link'] = None

        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if validated_data.get('image') == '':
            validated_data['image'] = None
        if validated_data.get('video') == '':
            validated_data['video'] = None
        if validated_data.get('link') == '':
            validated_data['link'] = None

        return super().update(instance, validated_data)
    
    def validate_image(self, value):
        if value == '' or value is None:
            return None
        return value 

    def validate_video(self, value):
        if value == '' or value is None:
            return None 

        return value 

    def validate_link(self, value):
        if value == '' or value is None:
            return None
        return value 