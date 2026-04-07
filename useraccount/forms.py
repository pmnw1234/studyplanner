from django import forms
from .models import UserProfile, Skill

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
        ]
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered w-full'}),
            'student_status': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'gender': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'current_level': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'goals': forms.Textarea(attrs={'rows': 2, 'class': 'textarea textarea-bordered w-full', 'placeholder': 'e.g. Master Power BI'}),
            # Using CheckboxSelectMultiple makes it easier for users to pick multiple skills
            'skills_to_teach': forms.CheckboxSelectMultiple(),
            'skills_to_learn': forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data
    

class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        # We only include the fields we want the user to change
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
            # Checkboxes make it much easier to select multiple skills at once
            'skills_to_teach_raw': forms.CharField(
                required=False,
                widget=forms.TextInput(attrs={'placeholder': 'e.g. SQL, Power BI, Python', 'class': 'input input-bordered w-full'})
            ),
            'skills_to_learn_raw': forms.CharField(
                required=False,
                widget=forms.TextInput(attrs={'placeholder': 'e.g. SQL, Power BI, Python', 'class': 'input input-bordered w-full'})
            ),
        }