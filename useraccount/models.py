from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    STUDENT_CHOICES = [
        ('Student', 'Student'),
        ('Non-Student', 'Non-Student'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_status = models.CharField(max_length=20, choices=STUDENT_CHOICES)
    birthday = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    goals = models.TextField()
    availability = models.TextField()

    def __str__(self):
        return self.user.username