from django.db import models
from django.contrib.auth.models import User
import random
import string
from django.core.validators import FileExtensionValidator
import secrets
from django.utils import timezone
from django.urls import reverse



def generate_room_code():
    while True:
        code = ''.join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=6
            )
        )

        if not StudyRoom.objects.filter(room_code=code).exists():
            return code


class StudyRoom(models.Model):
    course_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_rooms'
    )

    members = models.ManyToManyField(
        User,
        related_name='study_rooms',
        blank=True
    )

    room_code = models.CharField(
        max_length=6,
        unique=True,
        default=generate_room_code
    )

    created_at = models.DateTimeField(auto_now_add=True)
    
    # NEW: Max members limit (3 for free, 999 for premium)
    max_members = models.IntegerField(default=3, help_text="Maximum number of members allowed (3 for free, 999 for premium)")

    def is_full(self):
        """Check if room has reached max members"""
        return self.members.count() >= self.max_members
    
    def get_member_count(self):
        """Get total members including creator"""
        return self.members.count() + 1

    def __str__(self):
        return f"{self.course_name} ({self.room_code})"


class RoomProgress(models.Model):
    room = models.ForeignKey(
        StudyRoom,
        on_delete=models.CASCADE,
        related_name='progresses'
    )

    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class RoomActivity(models.Model):
    room = models.ForeignKey(
        StudyRoom,
        on_delete=models.CASCADE,
        related_name='activities'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action}"


class ClassWork(models.Model):
    CONTENT_TYPES = [
        ('assignment', 'Assignment'),
        ('material', 'Material'),
        ('quiz', 'Quiz'),
    ]
    
    room = models.ForeignKey(StudyRoom, on_delete=models.CASCADE, related_name='classworks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_works')
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default='assignment')
    
    # Resource file attachment for teachers
    resource_file = models.FileField(
        upload_to='classwork_resources/%Y/%m/%d/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'ppt', 'pptx', 'jpg', 'png', 'zip'])]
    )
    resource_link = models.URLField(blank=True, null=True, help_text="Optional external link")
    resource_title = models.CharField(max_length=200, blank=True, null=True, help_text="Title for the resource")

    def __str__(self):
        return self.title
class WorkComment(models.Model):
    work = models.ForeignKey(ClassWork, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.text[:30]}"


class Submission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('late', 'Late'),
    ]
    
    work = models.ForeignKey(ClassWork, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    content = models.TextField(blank=True)
    file = models.FileField(
        upload_to='submissions/%Y/%m/%d/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'jpg', 'png'])]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['work', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.work.title}"


class RoomActivityLog(models.Model):
    ACTION_CHOICES = [
        ('join', 'Joined Room'),
        ('leave', 'Left Room'),
        ('create_work', 'Created Class Work'),
        ('edit_work', 'Edited Class Work'),
        ('delete_work', 'Deleted Class Work'),
        ('post_stream', 'Posted Stream Update'),
        ('submit_work', 'Submitted Work'),
        ('grade_work', 'Graded Work'),
        ('upload_file', 'Uploaded File'),
    ]
    
    room = models.ForeignKey(StudyRoom, on_delete=models.CASCADE, related_name='activity_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('deadline', 'Deadline Approaching'),
        ('new_work', 'New Class Work'),
        ('submission', 'New Submission'),
        ('graded', 'Work Graded'),
        ('comment', 'New Comment'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    room = models.ForeignKey(StudyRoom, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    work = models.ForeignKey(ClassWork, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    submission = models.ForeignKey('Submission', on_delete=models.CASCADE, null=True, blank=True)
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.recipient.username} - {self.title}"
    


# studyroom/models.py (add this model)
from django.db import models
from django.contrib.auth.models import User

class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=200)
    content = models.TextField()
    source = models.CharField(max_length=50, default='ai_assistant')  # 'ai_assistant', 'manual'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


# studyplanner/studyroom/models.py

# Add these imports at the top
import secrets
from django.utils import timezone
from django.urls import reverse

# Add this model after your existing models
class ScheduledCall(models.Model):
    """Model for scheduling video call sessions"""
    CALL_STATUS = [
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Use a different name for the Jitsi room identifier
    jitsi_room_id = models.CharField(max_length=50, unique=True, default=secrets.token_urlsafe(16))
    room = models.ForeignKey(StudyRoom, on_delete=models.CASCADE, related_name='scheduled_calls')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_calls')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=CALL_STATUS, default='scheduled')
    
    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['room', 'start_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.room.course_name} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"
    
    def get_meeting_url(self):
        """Generate Jitsi meeting URL"""
        base_url = "https://meet.jit.si"
        return f"{base_url}/{self.jitsi_room_id}"
    
    def get_absolute_url(self):
        return reverse('studyroom:join_call', kwargs={'jitsi_room_id': self.jitsi_room_id})
    
    def is_ongoing(self):
        """Check if the call is currently happening"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time
    
    def save(self, *args, **kwargs):
        # Auto-update status based on time
        if not self.pk:  # New object
            self.jitsi_room_id = secrets.token_urlsafe(16)
        super().save(*args, **kwargs)
        
        # Update status based on current time (avoid recursion)
        if self.status not in ['cancelled', 'completed']:
            now = timezone.now()
            new_status = self.status
            if self.end_time < now:
                new_status = 'completed'
            elif self.start_time <= now <= self.end_time:
                new_status = 'ongoing'
            
            if new_status != self.status:
                self.status = new_status
                super().save(update_fields=['status'])