from django.contrib.auth import login, logout, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg, Q
from reviews.models import Review
from feedview.models import Post
from feedview.models import Like, Interested
from django.http import JsonResponse
from feedview.models import Comment
from itertools import chain
import json
from useraccount.models import  Quiz,Question

from .forms import (
    UserRegistrationForm,
    UserProfileEditForm,
    LoginForm,
    EnhancedUserProfileEditForm,
    CertificationForm,

)
from .models import (
    UserProfile,
    UserSkill,
    Certification,
    
)

from .models import UserProfile, UserSkill, Certification, Connection

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
    """Login view that works with custom LoginForm"""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            if user:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                print(f"✅ User logged in: {user.username}")
                print(f"✅ Redirecting to dashboard_home")
                return redirect("dashboard_home")
            else:
                print("❌ No user in cleaned_data")
        else:
            print(f"❌ Form invalid: {form.errors}")
            messages.error(request, "Invalid email/username or password.")
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
    reviews = Review.objects.filter(
        reviewed_user=request.user
    ).order_by('-created_at')
    avg_rating = reviews.aggregate(
        Avg('rating')
    )['rating__avg']
    
    posts = Post.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # ======================
    # 🔥 ACTIVITY FEED DATA
    # ======================
    likes = Like.objects.filter(
        post__user=request.user
    ).select_related('user', 'post')

    interests = Interested.objects.filter(
        post__user=request.user
    ).select_related('user', 'post')

    comments = Comment.objects.filter(
        post__user=request.user
    ).select_related('user', 'post')
    
    activities = sorted(
        chain(likes, interests, comments),
        key=lambda x: x.created_at,
        reverse=True
    )
    
    for post in posts:
        post.user_interested = Interested.objects.filter(
            user=request.user,
            post=post
        ).exists()

        post.is_liked = Like.objects.filter(
            user=request.user,
            post=post
        ).exists()
    
    context = {
        'profile': profile,
        'teach_skills_data': teach_skills_data,
        'learn_skills_data': learn_skills_data,
        'certifications': certifications,
        'study_partners_count': profile.study_partners_count,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'posts': posts,
        'activities': activities,
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

        form = EnhancedUserProfileEditForm(
        request.POST,
        request.FILES,
        instance=profile
    )

        if form.is_valid():

           request.session['pending_profile'] = request.POST.dict()

           skills_data = json.loads(
           request.POST.get('skills_data', '{}')
           )
           print("SKILLS DATA =", skills_data)
           teach_skills = skills_data.get('teach', [])
           for skill in teach_skills:

               category = skill.get('category', '').lower()
               name = skill.get('name', '').lower()

               print("CATEGORY =", category)
               print("NAME =", name)

               if category == "language" and name == "english":

                  form.save()

                  return redirect(
                  "take_quiz",
                  quiz_type="english"
                  )

               elif category == "tech" and name == "python":

                    form.save()

                    return redirect(
                    "take_quiz",
                    quiz_type="python"
                    )
           form.save()

           messages.success(
            request,
            'Your profile has been updated successfully!'
            )
           return redirect('profile')

        else:
          messages.error(
            request,
            'Please correct the errors below.'
        )

    else:
      form = EnhancedUserProfileEditForm(instance=profile)

    return render(request, 'useraccount/edit_profile.html', {
        'form': form,
        'profile': profile,
        'teach_skills_data': teach_skills_data,
        'learn_skills_data': learn_skills_data,
    })


# LIKE POST
@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    like, created = Like.objects.get_or_create(
        user=request.user,
        post=post
    )

    if not created:
        like.delete()
        status = 'unliked'
    else:
        status = 'liked'

    return JsonResponse({
        'status': status,
        'total_likes': post.likes.count()
    })


# INTEREST POST
@login_required
def interest_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    interest, created = Interested.objects.get_or_create(
        user=request.user,
        post=post
    )

    if not created:
        interest.delete()
        status = 'uninterested'
    else:
        status = 'interested'

    return JsonResponse({
        'status': status,
        'total_interests': post.interested.count()
    })


# COMMENT POST
@login_required
def comment_post(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, id=post_id)

        content = request.POST.get('content')

        comment = Comment.objects.create(
            user=request.user,
            post=post,
            content=content
        )

        return JsonResponse({
            'status': 'success',
            'text': comment.content,
            'username': request.user.username,
            'total_comments': post.comments.count()
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
# CONNECTION MANAGEMENT
# ======================

@login_required
def view_other_profile(request, user_id):
    """View another user's profile"""
    other_user = get_object_or_404(User, id=user_id)
    other_profile = other_user.userprofile
    
    # Check if already connected
    is_connected = Connection.objects.filter(
        Q(user1=request.user, user2=other_user) | 
        Q(user1=other_user, user2=request.user)
    ).exists()
    
    # Get skills
    teach_skills = other_profile.skills.filter(skill_type='teach')
    learn_skills = other_profile.skills.filter(skill_type='learn')
    
    # Get reviews
    reviews = Review.objects.filter(reviewed_user=other_user).order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    
    context = {
        'profile': other_profile,
        'user': other_user,
        'is_connected': is_connected,
        'teach_skills': teach_skills,
        'learn_skills': learn_skills,
        'reviews': reviews,
        'avg_rating': avg_rating,
    }
    
    return render(request, 'useraccount/other_profile.html', context)


@login_required
def connect_user(request, user_id):
    """Quick connect without going to profile page (for matches tab)"""
    other_user = get_object_or_404(User, id=user_id)
    
    if other_user == request.user:
        messages.error(request, "You cannot connect with yourself.")
        return redirect('dashboard_home')
    
    # Check if already connected
    is_connected = Connection.objects.filter(
        Q(user1=request.user, user2=other_user) | 
        Q(user1=other_user, user2=request.user)
    ).exists()
    
    if is_connected:
        messages.info(request, f"You are already connected with {other_user.username}.")
    else:
        # Create direct connection
        Connection.objects.create(user1=request.user, user2=other_user)
        
        # Update study partners count
        request.user.userprofile.study_partners_count += 1
        request.user.userprofile.save()
        other_user.userprofile.study_partners_count += 1
        other_user.userprofile.save()
        
        messages.success(request, f"You are now connected with {other_user.username}!")
    
    return redirect('dashboard_home')


# ======================
# ERROR HANDLER
# ======================

def custom_404(request, exception=None):
    return render(request, '404.html', status=404)




@login_required
def take_quiz(request, quiz_type):

    quiz = get_object_or_404(
        Quiz,
        quiz_type=quiz_type
    )

    questions = quiz.questions.all()

    if request.method == "POST":

        score = 0

        for question in questions:

            answer = request.POST.get(
                f"question_{question.id}"
            )

            if answer == question.correct_answer:
                score += 1

        # ---------- ENGLISH ----------
        if quiz_type == "english":

            if score <= 2:
                level = "A1"
            elif score <= 4:
                level = "A2"
            elif score <= 6:
                level = "B1"
            elif score <= 8:
                level = "B2"
            elif score <= 10:
                level = "C1"
            else:
                level = "C2"

            skill = UserSkill.objects.filter(
                user_profile=request.user.userprofile,
                skill_type="teach",
                category="language",
                skill_name__iexact="english"
            ).first()

        # ---------- PYTHON ----------
        elif quiz_type == "python":

            if score <= 3:
                level = "Beginner"
            elif score <= 7:
                level = "Intermediate"
            else:
                level = "Advanced"

            skill = UserSkill.objects.filter(
                user_profile=request.user.userprofile,
                skill_type="teach",
                category="tech",
                skill_name__iexact="python"
            ).first()

        if skill:
            skill.proficiency_level = level
            skill.save()

        messages.success(
            request,
            f"Your score is {score}/{questions.count()}. "
            f"Your {quiz.title} level is {level}."
        )

        return redirect("profile")

    return render(
        request,
        "useraccount/take_quiz.html",
        {
            "quiz": quiz,
            "questions": questions,
        }
    )