from django import forms
from .models import UserProfile

class UserRegistrationForm(forms.ModelForm):
    username = forms.CharField()
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())


    class Meta:
        model = UserProfile
        fields = [
            'student_status',
            'birthday',
            'gender',
            'goals',
            'availability',
        ]

        widgets = {
            'password': forms.PasswordInput(),
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'goals': forms.Textarea(attrs={'rows': 3}),
            'availability': forms.Textarea(attrs={'rows': 3}),
        }


    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")

        return cleaned_data