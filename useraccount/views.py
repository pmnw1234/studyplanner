from django.contrib.auth import login 
from django.shortcuts import render, redirect
from .forms import UserRegistrationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import UserProfileEditForm
from django.contrib.auth import authenticate, login
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

            # ✅ Create profile manually
            UserProfile.objects.create(user=user)

            # ✅ Login
            login(request, user)

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


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # user = authenticate(request, username=email, password=password)
        user = authenticate(request, email=request.POST.get("email"), password=password)

        if user is not None:
            login(request, user)
            return redirect("register")  # or dashboard later
        else:
            return render(request, "login.html", {"error": "Invalid email or password"})

    return render(request, "login.html")


@login_required
def edit_profile_view(request):
  
    # profile = request.user.userprofile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
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

