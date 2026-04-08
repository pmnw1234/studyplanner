from django import forms
from .models import UserProfile, Skill
from django.contrib.auth.models import User

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
        widgets ={
            'birthday': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}),
            'student_status': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'gender': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'current_level': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'goals': forms.Textarea(attrs={'rows': 2, 'class': 'textarea textarea-bordered w-full', 'placeholder': 'e.g. Master Power BI'}),
            'availability': forms.Textarea(attrs={'rows':2}),
            'skills_to_teach':forms.CheckboxSelectMultiple(),
            'skills_to_learn':forms.CheckboxSelectMultiple(),
            'skills_to_teach': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g. Python, JavaScript, SQL (separate with commas)'}),
            'skills_to_learn': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': 'e.g. React, Django, Machine Learning (separate with commas)'}),
        }
        widgets ={
            
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make current_level not required
        self.fields['current_level'].required = False
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


# forms.py - Simplified UserProfileEditForm with text inputs
class UserProfileEditForm(forms.ModelForm):
    # Add first_name and last_name fields for the User model
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
        
        # Populate first_name and last_name from the user model
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Update user's first_name and last_name
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
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            from django.contrib.auth import authenticate
            user = authenticate(username=email, password=password)
            if not user:
                raise forms.ValidationError("Invalid email/username or password.")
            cleaned_data['user'] = user
        return cleaned_data