from django.db import models
import uuid
class Connection(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('blocked', 'Blocked'),
    )
    connection_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='sent_connections')
    to_user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='received_connections')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['from_user', 'to_user']
        indexes = [
            models.Index(fields=['from_user', 'status']),
            models.Index(fields=['to_user', 'status']),
        ]

class Follow(models.Model):
    follower = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'following']
   