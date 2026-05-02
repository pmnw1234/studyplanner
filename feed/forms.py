from django import forms
from .models import Post

class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['title', 'description', 'post_type']

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter post title...'
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'What is on your mind?',
                'rows': 4
            }),

            'post_type': forms.Select(attrs={
                'class': 'form-control'
            }),
        }