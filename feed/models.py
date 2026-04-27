from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):

    title = models.CharField(max_length=200)  # MUST exist

    description = models.TextField()

    POST_TYPE_CHOICES = [
        ('study', 'Study Partner'),
        ('skill', 'Skill Swap'),
    ]

    post_type = models.CharField(
        max_length=10,
        choices=POST_TYPE_CHOICES
    )

    likes = models.ManyToManyField(User, blank=True, related_name='liked_posts')
    interested = models.ManyToManyField(User, blank=True, related_name='interested_posts')

    created_at = models.DateTimeField(auto_now_add=True)

   