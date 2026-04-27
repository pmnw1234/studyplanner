from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileEditForm, LoginForm, EnhancedUserProfileEditForm, CertificationForm
from .models import UserProfile, UserSkill, Certification
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
    return render(request, 'landing.html')

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get skills from UserSkill model with levels and categories
    teach_skills_data = [
        {'name': skill.skill_name, 'level': skill.proficiency_level, 'category': skill.category}
        for skill in profile.skills.filter(skill_type='teach')
    ]
    learn_skills_data = [
        {'name': skill.skill_name, 'level': skill.proficiency_level, 'category': skill.category}
        for skill in profile.skills.filter(skill_type='learn')
    ]
    certifications = profile.certifications.all()
    context = {
        'profile': profile,
        'teach_skills_data': teach_skills_data,
        'learn_skills_data': learn_skills_data,
        'certifications': certifications,
    }
    return render(request, 'useraccount/profile.html', context)

@login_required
def edit_profile(request):
    profile = request.user.userprofile
    
    # Load existing skills from the new UserSkill model
    teach_skills_data = []
    learn_skills_data = []
    
    # Get teach skills from UserSkill model
    teach_skills = UserSkill.objects.filter(user_profile=profile, skill_type='teach')
    for skill in teach_skills:
        teach_skills_data.append({
            'name': skill.skill_name,
            'category': skill.category,
            'level': skill.proficiency_level
        })
    
    # Get learn skills from UserSkill model
    learn_skills = UserSkill.objects.filter(user_profile=profile, skill_type='learn')
    for skill in learn_skills:
        learn_skills_data.append({
            'name': skill.skill_name,
            'category': skill.category,
            'level': skill.proficiency_level
        })
    
    if request.method == 'POST':
        form = EnhancedUserProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileEditForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
        'teach_skills_data': teach_skills_data,
        'learn_skills_data': learn_skills_data,
    }
    return render(request, 'useraccount/edit_profile.html', context)

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



@login_required
def add_certification(request):
    """Add a new certification to user profile"""
    profile = request.user.userprofile
    
    if request.method == 'POST':
        form = CertificationForm(request.POST, request.FILES)
        if form.is_valid():
            certification = form.save(commit=False)
            certification.user_profile = profile
            certification.save()
            messages.success(request, f'Certification "{certification.title}" added successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CertificationForm()
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'useraccount/add_certification.html', context)


@login_required
def edit_certification(request, cert_id):
    """Edit an existing certification"""
    profile = request.user.userprofile
    certification = get_object_or_404(Certification, id=cert_id, user_profile=profile)
    
    if request.method == 'POST':
        form = CertificationForm(request.POST, request.FILES, instance=certification)
        if form.is_valid():
            form.save()
            messages.success(request, f'Certification "{certification.title}" updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CertificationForm(instance=certification)
    
    context = {
        'form': form,
        'certification': certification,
        'profile': profile,
    }
    return render(request, 'useraccount/edit_certification.html', context)


@login_required
def delete_certification(request, cert_id):
    """Delete a certification"""
    profile = request.user.userprofile
    certification = get_object_or_404(Certification, id=cert_id, user_profile=profile)
    
    if request.method == 'POST':
        title = certification.title
        certification.delete()
        messages.success(request, f'Certification "{title}" deleted successfully!')
        return redirect('profile')
    
    context = {
        'certification': certification,
    }
    return render(request, 'useraccount/delete_certification.html', context)

def custom_404(request, exception=None):
    return render(request, '404.html', status=404)