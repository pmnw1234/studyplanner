from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileEditForm, LoginForm
from .models import UserProfile
from django.contrib.auth.models import User

def landing_view(request):
    """Landing page view - shown to non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    return render(request, 'landing.html')

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Registration successful.')
            return redirect('dashboard_home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            login(request, form.cleaned_data['user'])
            messages.success(request, 'Welcome back!')
            return redirect("dashboard_home")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')

@login_required
def profile_view(request):
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'useraccount/profile.html', {'profile': profile})

@login_required
def edit_profile_view(request):
    profile = request.user.userprofile
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileEditForm(instance=profile)
    return render(request, 'useraccount/edit_profile.html', {'form': form})

@login_required
def change_password_view(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password updated!')
            return redirect('profile')
    return render(request, "useraccount/change_password.html")