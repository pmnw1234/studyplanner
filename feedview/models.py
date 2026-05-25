from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    POST_TYPE_CHOICES = [
        ('study', 'Study Partner'),
        ('skill', 'Skill Swap'),
    ]
    
    POST_CATEGORY_CHOICES = [
        ('skill_swap', 'Skill Swap'),
        ('study_partner', 'Study Partner'),
    ]
    
    POST_TOPIC_CHOICES = [
        ('language', 'Language'),
        ('tech', 'Technology'),
        ('science', 'Science'),
        ('art', 'Art'),
        ('business', 'Business'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    video = models.FileField(upload_to='posts/videos/', blank=True, null=True)
    
    post_type = models.CharField(max_length=10, choices=POST_TYPE_CHOICES, default='study')
    category = models.CharField(max_length=20, choices=POST_CATEGORY_CHOICES, default='skill_swap')
    topic = models.CharField(max_length=20, choices=POST_TOPIC_CHOICES, default='general')
    hashtags = models.CharField(max_length=200, blank=True, help_text="Comma separated: #tech,#python")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)

    def total_likes(self):
        return self.likes.count()

    def total_interested(self):
        return self.interests.count()

    def __str__(self):
        return f"{self.user.username} - {self.post_type}"


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        unique_together = ['user', 'post']


class Interested(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='interests')

    class Meta:
        unique_together = ['user', 'post']


class MatchRequest(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='match_sent_requests'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='match_received_requests'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('declined', 'Declined'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['sender', 'receiver']

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    class Meta:
        ordering = ['created_at'] # Oldest comments/replies show first

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('interest', 'Interest'),
    ]

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feedview_sent_notifications'  # Changed from 'sent_notifications'
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feedview_received_notifications'  # Changed from 'received_notifications'
    )

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )

    message = models.CharField(max_length=255)
    note = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)