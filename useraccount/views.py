from django.contrib.auth import login 
from django.shortcuts import render, redirect
from .forms import UserRegistrationForm
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileEditForm
from .models import UserProfile

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login


def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)  # Don't forget request.FILES for profile_picture!
        
        if form.is_valid():
            # 2. Save the User
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )

            # 3. Link and Save the Profile
            profile = form.save(commit=False)
            profile.user = user
            profile.save()

            # 4. AUTO-LOGIN (The Magic Step)
            # This tells Django: "I trust this person, they just signed up."
            login(request, user)

            # 5. GO DIRECTLY TO DASHBOARD
            # Make sure 'dashboard_home' matches the 'name' in dashboard/urls.py
            return redirect('dashboard_home') 
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})

@login_required
def edit_profile_view(request):
  
    profile = request.user.userprofile
    
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')  # Make sure this matches your URL name
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileEditForm(instance=profile)
    
    return render(request, 'useraccount/edit_profile.html', {'form': form})

@login_required
def profile_view(request):
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'useraccount/profile.html', {'profile': profile})

@login_required
def change_password_view(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Check if old password is correct
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            # Change password
            request.user.set_password(new_password)
            request.user.save()
            
            # Update session to keep user logged in
            update_session_auth_hash(request, request.user)
            
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile_view')
    
    return render(request, 'useraccount/change_password.html')

# views.py - Add this function
from django.contrib.auth import logout

@login_required
def logout_view(request):
    """Log out the user and redirect to login page"""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')