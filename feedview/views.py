from django.contrib.auth import login, logout, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

from useraccount.forms import (
    UserRegistrationForm,
    UserProfileEditForm,
    LoginForm,
    EnhancedUserProfileEditForm,
    CertificationForm
)
from useraccount.models import UserProfile, UserSkill, Certification
from feedview.models import MatchRequest, Post

@login_required
def feed_view(request):
    users = User.objects.exclude(id=request.user.id)
    posts = Post.objects.all().order_by('-created_at')

    for post in posts:
        post.request_sent = MatchRequest.objects.filter(
            sender=request.user,
            receiver=post.user,
            status='pending'
        ).exists()

    return render(request, 'feedview/feed.html', {
        'posts': posts,
        'users': users
    })


@login_required
def inbox_view(request):
    requests = MatchRequest.objects.filter(
        receiver=request.user
    ).order_by('-created_at')

    return render(request, 'feedview/inbox.html', {
        'requests': requests
    })


@login_required
def create_post(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        post_type = request.POST.get('post_type')
        image = request.FILES.get('image')
        video = request.FILES.get('video')

        Post.objects.create(
            user=request.user,
            content=content,
            post_type=post_type,
            image=image,
            video=video
        )

        return redirect('feed')

    return render(request, 'feedview/create_post.html')


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    like = post.likes.filter(user=request.user).first()

    if like:
        like.delete()
    else:
        post.likes.create(user=request.user)

    return redirect('feed')


@login_required
def send_request(request, user_id):
    receiver = get_object_or_404(User, id=user_id)

    # can't send to yourself
    if receiver == request.user:
        return redirect('feed')

    # already sent by me
    existing = MatchRequest.objects.filter(
        sender=request.user,
        receiver=receiver
    ).first()

    if existing:
        return redirect('feed')

    # reverse request exists (they already sent me)
    reverse_request = MatchRequest.objects.filter(
        sender=receiver,
        receiver=request.user
    ).first()

    if reverse_request:
        return redirect('feed')

    MatchRequest.objects.create(
        sender=request.user,
        receiver=receiver,
        status='pending'
    )

    return redirect('feed')



@login_required
def accept_request(request, request_id):
    req = get_object_or_404(
        MatchRequest,
        id=request_id,
        receiver=request.user
    )

    req.status = 'accepted'
    req.save()

    sender_profile, _ = UserProfile.objects.get_or_create(user=req.sender)
    receiver_profile, _ = UserProfile.objects.get_or_create(user=req.receiver)

    sender_profile.study_partners_count += 1
    receiver_profile.study_partners_count += 1

    sender_profile.save()
    receiver_profile.save()

    return redirect('inbox')



@login_required
def decline_request(request, request_id):
    req = get_object_or_404(
        MatchRequest,
        id=request_id,
        receiver=request.user
    )

    req.status = 'declined'
    req.save()

    return redirect('inbox')
def landing_view(request):
    """Landing page view - shown to non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    return render(request, 'landing.html')


def register_view(request):
    """User registration"""
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
    """User login (clean version)"""
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect("dashboard_home")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

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
    """User profile display"""
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
        'study_partners_count': profile.study_partners_count,
    }

    return render(request, 'useraccount/profile.html', context)


@login_required
def edit_profile(request):
    """Edit user profile"""
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

    context = {
        'form': form,
        'profile': profile,
        'teach_skills_data': teach_skills_data,
        'learn_skills_data': learn_skills_data,
    }

    return render(request, 'useraccount/edit_profile.html', context)


@login_required
def change_password_view(request):
    """Change password"""
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