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
    
    created_at = models.DateTimeField(auto_now_add=True)

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