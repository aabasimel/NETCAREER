from django.db.models import Q
from .models import Post

class FeedGenerator:
    @staticmethod
    def get_user_feed(user, offset=0, limit=20):
        """Generate personalized feed for user"""
        # Get user's connections
        connections = user.sent_connections.filter(status='accepted').values_list('to_user', flat=True)
        connections |= user.received_connections.filter(status='accepted').values_list('from_user', flat=True)
        
        # Get posts from connections and followed companies
        feed_posts = Post.objects.filter(
            Q(author__in=connections) |
            Q(content_type='job', company__followers=user) |
            Q(author=user)  # Include user's own posts
        ).filter(
            is_published=True
        ).select_related(
            'author', 'author__profile'
        ).prefetch_related(
            'likes', 'comments'
        ).order_by('-created_at')
        
        return feed_posts[offset:offset + limit]