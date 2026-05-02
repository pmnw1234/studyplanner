from django.db import models
from django.contrib.auth.models import User

# REMOVE THIS LINE: from useraccount.forms import UserProfileEditForm

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
        ('Evening', 'Evening'),
        ('Night', 'Night'),
        ('Late Night', 'Late Night'),
        ('Flexible', 'Flexible'),
        ('Weekend Only', 'Weekend Only'),
        ('Weekday Only', 'Weekday Only'),
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
    
    # Matching Engine Fields (keeping for backward compatibility)
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
    study_partners_count = models.IntegerField(default=0)
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


class UserSkill(models.Model):
    """Store detailed skill information with categories and proficiency levels"""
    
    SKILL_CATEGORIES = [
        ('tech', 'Tech / Programming'),
        ('language', 'Language'),
        ('general', 'General Skills'),
    ]
    
    SKILL_TYPES = [
        ('teach', 'I Can Teach'),
        ('learn', 'I Want to Learn'),
    ]
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=SKILL_CATEGORIES)
    skill_type = models.CharField(max_length=10, choices=SKILL_TYPES)
    proficiency_level = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user_profile', 'skill_name', 'skill_type']
        ordering = ['skill_type', 'skill_name']
    
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.get_skill_type_display()}: {self.skill_name} ({self.proficiency_level})"


class ConnectionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_user.username} → {self.to_user.username} ({self.status})"



class Connection(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user1', 'user2']
    
    def __str__(self):
        return f"{self.user1.username} ↔ {self.user2.username}"
    
    def get_other_user(self, current_user):
        if self.user1 == current_user:
            return self.user2
        return self.user1

def get_enhanced_match_summary(profile1, profile2):
    """Get enhanced match summary using UserSkill model with levels"""
    
    # Get skills from UserSkill model
    profile1_teach = profile1.skills.filter(skill_type='teach')
    profile1_learn = profile1.skills.filter(skill_type='learn')
    profile2_teach = profile2.skills.filter(skill_type='teach')
    profile2_learn = profile2.skills.filter(skill_type='learn')
    
    matches = []
    
    # Check if profile1 teaches what profile2 wants to learn
    for teach_skill in profile1_teach:
        for learn_skill in profile2_learn:
            if teach_skill.skill_name.lower() == learn_skill.skill_name.lower():
                matches.append({
                    'skill': teach_skill.skill_name,
                    'teacher': profile1.user.username,
                    'teacher_level': teach_skill.proficiency_level,
                    'learner': profile2.user.username,
                    'learner_level': learn_skill.proficiency_level,
                    'type': 'teaches_to'
                })
    
    # Check if profile2 teaches what profile1 wants to learn
    for teach_skill in profile2_teach:
        for learn_skill in profile1_learn:
            if teach_skill.skill_name.lower() == learn_skill.skill_name.lower():
                matches.append({
                    'skill': teach_skill.skill_name,
                    'teacher': profile2.user.username,
                    'teacher_level': teach_skill.proficiency_level,
                    'learner': profile1.user.username,
                    'learner_level': learn_skill.proficiency_level,
                    'type': 'teaches_to'
                })
    
    return {
        'matches': matches,
        'total_score': len(matches)
    }

class Certification(models.Model):
    """User certifications and credentials with file upload"""
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='certifications')
    title = models.CharField(max_length=200, help_text="e.g., 'Google Data Analytics Professional Certificate'")
    issuing_organization = models.CharField(max_length=100, help_text="e.g., 'Google', 'Coursera', 'University'")
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True, help_text="Leave blank if no expiry")
    credential_url = models.URLField(blank=True, null=True, help_text="Link to verify credential")
    credential_id = models.CharField(max_length=100, blank=True, null=True, help_text="Certificate ID/License number")
    
    # File upload for certificate
    certificate_file = models.FileField(
        upload_to='certificates/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Upload certificate (PDF, JPG, PNG)"
    )
    
    description = models.TextField(blank=True, null=True, help_text="Additional details about the certification")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.title}"
    
    @property
    def is_expired(self):
        """Check if certification is expired"""
        if self.expiry_date:
            from datetime import date
            return self.expiry_date < date.today()
        return False
    
    @property
    def file_extension(self):
        """Get file extension"""
        if self.certificate_file:
            return self.certificate_file.name.split('.')[-1].lower()
        return None