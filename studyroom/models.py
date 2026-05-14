from django.db import models
from django.contrib.auth.models import User
import random
import string


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

# Create your models here.
