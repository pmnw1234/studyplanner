from django.contrib.auth import login 
from django.shortcuts import render, redirect
from .forms import UserRegistrationForm
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import UserProfile
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
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

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserProfileEditForm



@login_required
def edit_profile_view(request):
  
    profile = request.user.userprofile
    
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, instance=profile)
        if form.is_valid():
            form.save() 
            return redirect('dashboard_home')
    else:
        form = UserProfileEditForm(instance=profile)

    return render(request, 'useraccount/edit_profile.html', {'form': form})


@login_required
def profile_view(request):
    # Get the profile for the logged-in user
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'useraccount/profile.html', {'profile': profile})