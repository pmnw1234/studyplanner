from django.db import models
from django.contrib.auth.models import User

class Skill(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    # Choices
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    STUDENT_CHOICES = [
        ('University Student', 'University Student'),
        ('Final Year Student', 'Final Year Student'),
        ('Working Professional', 'Working Professional'),
        ('Non-Student', 'Non-Student'),
    ]
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.png', blank=True)
    LEVEL_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]
    
    TIME_CHOICES = [
        ('Morning', 'Morning'),
        ('Afternoon', 'Afternoon'),
        ('Night', 'Night'),
    ]

    # Links to the built-in Django User model
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Basic Info
    student_status = models.CharField(max_length=30, choices=STUDENT_CHOICES, default='University Student')
    birthday = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Other')
    
    # Matching Engine Fields
    # related_name allows us to do: skill.teachers.all() or skill.learners.all()
    skills_to_teach = models.TextField(blank=True, help_text="List skills separated by commas")
    skills_to_learn = models.TextField(blank=True, help_text="List skills separated by commas")
    current_level = models.CharField(
        max_length=20, 
        choices=LEVEL_CHOICES, 
        default='Beginner'
    )
    
    preferred_study_time = models.CharField(
        max_length=20, 
        choices=TIME_CHOICES, 
        default='Morning'
    )
    
    # Extra Details
    goals = models.TextField(blank=True) # Placeholders go in forms.py, not here
    availability = models.TextField(blank=True)

    def __str__(self):
        return self.user.username