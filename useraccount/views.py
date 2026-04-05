from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from .forms import UserRegistrationForm

from django.contrib.auth.models import User

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():

            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']


            if User.objects.filter(username=username).exists():
                form.add_error('username', 'Username already exists')
                return render(request, 'planner/register.html', {'form': form})


            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            profile = form.save(commit=False)
            profile.user = user
            profile.save()

            return redirect('login')
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})