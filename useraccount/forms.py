from django import forms
from .models import UserProfile, Skill, UserSkill, Certification
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
import json

class UserRegistrationForm(forms.ModelForm):
    # User fields (not in UserProfile model)
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'input input-bordered w-full'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'input input-bordered w-full'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full'}))

    class Meta:
        model = UserProfile
        fields = [
            'student_status',
            'profile_picture',
            'birthday',
            'gender',
            'current_level',
            'skills_to_teach',
            'skills_to_learn',
            'goals',
            'availability'
        ]
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}),
            'student_status': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'gender': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'current_level': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'goals': forms.Textarea(attrs={'rows': 2, 'class': 'textarea textarea-bordered w-full', 'placeholder': 'e.g. Master Power BI'}),
            'availability': forms.Textarea(attrs={'rows': 2, 'class': 'textarea textarea-bordered w-full'}),
            'skills_to_teach': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g. Python, JavaScript, SQL (separate with commas)'}),
            'skills_to_learn': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g. React, Django, Machine Learning (separate with commas)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['current_level'].required = False
        self.fields['profile_picture'].required = False
        self.fields['skills_to_teach'].required = False
        self.fields['skills_to_learn'].required = False
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")
        
        return cleaned_data


class UserProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Last name'})
    )

    class Meta:
        model = UserProfile
        fields = [
            'profile_picture',
            'student_status', 
            'birthday', 
            'gender', 
            'current_level', 
            'preferred_study_time',
            'skills_to_teach',
            'skills_to_learn',
            'goals', 
            'availability'
        ]
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}),
            'student_status': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'gender': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'current_level': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'preferred_study_time': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'goals': forms.Textarea(attrs={'rows': 3, 'class': 'textarea textarea-bordered w-full', 'placeholder': 'What are you working towards?'}),
            'availability': forms.Textarea(attrs={'rows': 2, 'class': 'textarea textarea-bordered w-full', 'placeholder': 'e.g. Monday nights, Weekends'}),
            'skills_to_teach': forms.TextInput(attrs={
                'class': 'input input-bordered w-full', 
                'placeholder': 'e.g. Python, JavaScript, SQL (separate with commas)'
            }),
            'skills_to_learn': forms.TextInput(attrs={
                'class': 'input input-bordered w-full', 
                'placeholder': 'e.g. React, Django, Machine Learning (separate with commas)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.instance.user:
            self.instance.user.first_name = self.cleaned_data.get('first_name', '')
            self.instance.user.last_name = self.cleaned_data.get('last_name', '')
            if commit:
                self.instance.user.save()
        if commit:
            profile.save()
        return profile


class LoginForm(forms.Form):
    email = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Email or Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'Password'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email_or_username = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email_or_username and password:
            user = None
            if '@' in email_or_username:
                try:
                    user_obj = User.objects.get(email=email_or_username)
                    username = user_obj.username
                    user = authenticate(username=username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is None:
                user = authenticate(username=email_or_username, password=password)
            
            if not user:
                raise forms.ValidationError("Invalid email/username or password.")
            
            cleaned_data['user'] = user
        return cleaned_data


class EnhancedUserProfileEditForm(UserProfileEditForm):
    """Extended version that saves skills with categories and proficiency levels"""
    skills_data = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        if commit:
            profile.save()
        
        # Process skills data
        skills_data = self.cleaned_data.get('skills_data')
        if skills_data:
            try:
                data = json.loads(skills_data)
                
                # Clear existing skills for this user
                UserSkill.objects.filter(user_profile=profile).delete()
                
                # Save teach skills with categories and levels
                for skill in data.get('teach', []):
                    if skill.get('name') and skill.get('name').strip():
                        UserSkill.objects.create(
                            user_profile=profile,
                            skill_name=skill['name'].strip(),
                            category=skill.get('category', 'tech'),
                            skill_type='teach',
                            proficiency_level=skill.get('level', 'Beginner')
                        )
                
                # Save learn skills with categories and levels
                for skill in data.get('learn', []):
                    if skill.get('name') and skill.get('name').strip():
                        UserSkill.objects.create(
                            user_profile=profile,
                            skill_name=skill['name'].strip(),
                            category=skill.get('category', 'tech'),
                            skill_type='learn',
                            proficiency_level=skill.get('level', 'Beginner')
                        )
                
                # Also maintain text fields for backward compatibility
                teach_names = [s['name'].strip() for s in data.get('teach', []) if s.get('name') and s['name'].strip()]
                learn_names = [s['name'].strip() for s in data.get('learn', []) if s.get('name') and s['name'].strip()]
                profile.skills_to_teach = ', '.join(teach_names) if teach_names else ''
                profile.skills_to_learn = ', '.join(learn_names) if learn_names else ''
                
                if commit:
                    profile.save()
                    
            except json.JSONDecodeError:
                pass
        
        return profile


class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['title', 'issuing_organization', 'issue_date', 'expiry_date', 'credential_url', 'credential_id', 'certificate_file', 'description']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2 rounded-xl', 'style': 'background-color: var(--bg-card); border: 1px solid var(--border-color);'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2 rounded-xl', 'style': 'background-color: var(--bg-card); border: 1px solid var(--border-color);'}),
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl', 'placeholder': 'e.g., Google Data Analytics Certificate', 'style': 'background-color: var(--bg-card); border: 1px solid var(--border-color);'}),
            'issuing_organization': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl', 'placeholder': 'e.g., Google, Coursera', 'style': 'background-color: var(--bg-card); border: 1px solid var(--border-color);'}),
            'credential_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2 rounded-xl', 'placeholder': 'https://...', 'style': 'background-color: var(--bg-card); border: 1px solid var(--border-color);'}),
            'credential_id': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl', 'placeholder': 'Certificate ID', 'style': 'background-color: var(--bg-card); border: 1px solid var(--border-color);'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2 rounded-xl', 'placeholder': 'Additional details about this certification...', 'style': 'background-color: var(--bg-card); border: 1px solid var(--border-color);'}),
            'certificate_file': forms.FileInput(attrs={'class': 'w-full px-4 py-2 rounded-xl', 'style': 'background-color: var(--bg-card); border: 1px solid var(--border-color);', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        }