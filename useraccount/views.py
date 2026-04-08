# views.py
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileEditForm
from .models import UserProfile


def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)  # Don't forget request.FILES for profile_picture!
        
        if form.is_valid():
            try:
                # Create the User
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password']
                )
                
                # Create the UserProfile but don't save yet
                profile = form.save(commit=False)
                profile.user = user
                
                # Save the profile with all fields including availability
                profile.save()
                
                # Save many-to-many fields if you have any
                form.save_m2m()
                
                # Auto-login
                login(request, user)
                
                messages.success(request, f'Welcome {user.username}! Registration successful.')
                return redirect('dashboard_home')
                
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            # Print form errors to debug
            print(form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        # Try to find user by email (case-insensitive)
        try:
            # Get user by email
            user_obj = User.objects.get(email__iexact=email)
            # Authenticate with username
            user = authenticate(request, username=user_obj.username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                
                # Check for 'next' parameter
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect("dashboard_home")
            else:
                messages.error(request, "Invalid email or password.")
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
        
        return render(request, "login.html")
    
    return render(request, "login.html")

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')

@login_required
def edit_profile_view(request):
    # Get or create profile to avoid DoesNotExist error
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
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
    # Get or create profile for the logged-in user
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

# views.py - Add landing_view at the top
def landing_view(request):
    
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    return render(request, 'landing.html')


from django.contrib.auth import logout

@login_required
def logout_view(request):
    """Log out the user and redirect to login page"""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('landing')