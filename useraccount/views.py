from django.contrib.auth import login, logout, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

from .forms import (
    UserRegistrationForm,
    UserProfileEditForm,
    LoginForm,
    EnhancedUserProfileEditForm,
    CertificationForm
)
from .models import UserProfile, UserSkill, Certification
from feedview.models import MatchRequest


# ======================
# PUBLIC VIEWS
# ======================

def landing_view(request):
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
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("dashboard_home")
        else:
            return render(request, "login.html", {
                "error": "Invalid username or password"
            })

    return render(request, "login.html")

    """Login view that works with custom LoginForm"""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            if user:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                print(f"✅ User logged in: {user.username}")  # Debug
                print(f"✅ Redirecting to dashboard_home")  # Debug
                return redirect("dashboard_home")
            else:
                print("❌ No user in cleaned_data")  # Debug
        else:
            print(f"❌ Form invalid: {form.errors}")  # Debug
            messages.error(request, "Invalid email/username or password.")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})
   


    return render(request, "login.html", {"form": form})
# ======================
# AUTHENTICATED VIEWS
# ======================

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return render(request, 'landing.html')


@login_required
def profile_view(request):
    """Resolved merge conflict + combined features"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Teach skills
    teach_skills_data = [
        {
            'name': skill.skill_name,
            'level': skill.proficiency_level,
            'category': skill.category
        }
        for skill in profile.skills.filter(skill_type='teach')
    ]

    # Learn skills
    learn_skills_data = [
        {
            'name': skill.skill_name,
            'level': skill.proficiency_level,
            'category': skill.category
        }
        for skill in profile.skills.filter(skill_type='learn')
    ]

    # Certifications
    certifications = profile.certifications.all()

    context = {
        'profile': profile,
        'teach_skills_data': teach_skills_data,
        'learn_skills_data': learn_skills_data,
        'certifications': certifications,
        'study_partners_count': profile.study_partners_count,  # merged feature
    }

    return render(request, 'useraccount/profile.html', context)


@login_required
def edit_profile(request):
    profile = request.user.userprofile

    # Load skills
    teach_skills_data = [
        {
            'name': skill.skill_name,
            'category': skill.category,
            'level': skill.proficiency_level
        }
        for skill in UserSkill.objects.filter(user_profile=profile, skill_type='teach')
    ]

    learn_skills_data = [
        {
            'name': skill.skill_name,
            'category': skill.category,
            'level': skill.proficiency_level
        }
        for skill in UserSkill.objects.filter(user_profile=profile, skill_type='learn')
    ]

    if request.method == 'POST':
        form = EnhancedUserProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EnhancedUserProfileEditForm(instance=profile)

    return render(request, 'useraccount/edit_profile.html', {
        'form': form,
        'profile': profile,
        'teach_skills_data': teach_skills_data,
        'learn_skills_data': learn_skills_data,
    })


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


# ======================
# CERTIFICATIONS
# ======================

@login_required
def add_certification(request):
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

    return render(request, 'useraccount/add_certification.html', {
        'form': form,
        'profile': profile,
    })


@login_required
def edit_certification(request, cert_id):
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

    return render(request, 'useraccount/edit_certification.html', {
        'form': form,
        'certification': certification,
        'profile': profile,
    })


@login_required
def delete_certification(request, cert_id):
    profile = request.user.userprofile
    certification = get_object_or_404(Certification, id=cert_id, user_profile=profile)

    if request.method == 'POST':
        title = certification.title
        certification.delete()
        messages.success(request, f'Certification "{title}" deleted successfully!')
        return redirect('profile')

    return render(request, 'useraccount/delete_certification.html', {
        'certification': certification,
    })


# ======================
# ERROR HANDLER
# ======================

def custom_404(request, exception=None):
    return render(request, '404.html', status=404)