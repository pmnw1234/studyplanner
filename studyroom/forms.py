from django import forms
from .models import StudyRoom


class StudyRoomForm(forms.ModelForm):
    class Meta:
        model = StudyRoom
        fields = ['course_name', 'description']

        widgets = {
            'course_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Study Room Name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'placeholder': 'Description',
                'rows': 4
            }),
        }