from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from .forms import UserRegistrationForm

from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

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

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect("register")  # or dashboard later
        else:
            return render(request, "login.html", {"error": "Invalid email or password"})

    return render(request, "login.html")