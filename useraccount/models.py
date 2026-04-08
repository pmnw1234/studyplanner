from django.db import models
from django.contrib.auth.models import User

class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
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
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    
    # Profile Picture
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        blank=True, 
        null=True,
        default='profile_pics/default.png'
    )
    
    # Basic Info
    student_status = models.CharField(
        max_length=30, 
        choices=STUDENT_CHOICES, 
        default='University Student'
    )
    birthday = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10, 
        choices=GENDER_CHOICES, 
        default='Other'
    )
    
    # Matching Engine Fields
    skills_to_teach = models.TextField(
        blank=True, 
        null=True,
        help_text="List skills separated by commas"
    )
    skills_to_learn = models.TextField(
        blank=True, 
        null=True,
        help_text="List skills separated by commas"
    )
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
    goals = models.TextField(blank=True, null=True)
    availability = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_skills_to_teach_list(self):
        """Return skills_to_teach as a list"""
        if self.skills_to_teach:
            return [skill.strip() for skill in self.skills_to_teach.split(',') if skill.strip()]
        return []
    
    def get_skills_to_learn_list(self):
        """Return skills_to_learn as a list"""
        if self.skills_to_learn:
            return [skill.strip() for skill in self.skills_to_learn.split(',') if skill.strip()]
        return []
    
    def get_full_name(self):
        """Return user's full name"""
        return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username
    
    def age(self):
        """Calculate user's age from birthday"""
        if self.birthday:
            from datetime import date
            today = date.today()
            return today.year - self.birthday.year - (
                (today.month, today.day) < (self.birthday.month, self.birthday.day)
            )
        return None
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"