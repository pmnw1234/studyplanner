# dashboard/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    thumbnail = models.URLField(blank=True, null=True)
    platform = models.CharField(max_length=100)  # YouTube, Coursera, Udemy, etc.
    url = models.URLField()
    duration = models.CharField(max_length=50, blank=True)  # e.g., "45 mins"
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']


class Video(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='videos', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    thumbnail = models.URLField(blank=True, null=True)
    youtube_id = models.CharField(max_length=50, blank=True)  # For YouTube videos
    url = models.URLField()
    duration = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)  # For video order in course
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['order', 'id']


class WatchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_history')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='watch_history')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='watch_history', null=True, blank=True)
    watched_at = models.DateTimeField(auto_now_add=True)
    progress = models.IntegerField(default=0)  # Percentage watched
    last_position = models.IntegerField(default=0)  # Seconds watched
    
    def __str__(self):
        return f"{self.user.username} watched {self.video.title} at {self.watched_at}"
    
    class Meta:
        ordering = ['-watched_at']
        unique_together = ['user', 'video']  # Prevent duplicate entries


class SavedCourse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} saved {self.course.title}"
    
    class Meta:
        ordering = ['-saved_at']
        unique_together = ['user', 'course']  # Prevent duplicate saves


class SavedVideo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_videos')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} saved {self.video.title}"
    
    class Meta:
        ordering = ['-saved_at']
        unique_together = ['user', 'video']