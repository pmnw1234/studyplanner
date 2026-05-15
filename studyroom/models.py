from django.db import models
from django.contrib.auth.models import User
import random
import string
from django.core.validators import FileExtensionValidator


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

    def is_full(self):
        return self.members.count() >= 3

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
    room = models.ForeignKey(StudyRoom, on_delete=models.CASCADE, related_name='classworks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_works')
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
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