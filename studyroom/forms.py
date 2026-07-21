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

# studyplanner/studyroom/forms.py

from django import forms
from .models import ScheduledCall, ClassWork, Submission
from django.utils import timezone

class ScheduledCallForm(forms.ModelForm):
    class Meta:
        model = ScheduledCall
        fields = ['title', 'description', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if end_time <= start_time:
                raise forms.ValidationError("End time must be after start time.")
            
            if start_time < timezone.now():
                raise forms.ValidationError("Start time must be in the future.")
        
        return cleaned_data