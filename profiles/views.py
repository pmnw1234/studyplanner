# profiles/views.py - UPDATED VERSION

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from useraccount.models import UserProfile, Connection, ConnectionRequest
from feedview.models import MatchRequest,Post
from useraccount.models import UserProfile, UserSkill, ConnectionRequest, Connection, Certification
from django.db.models import Avg
from django.db.models import Q
from reviews.models import Review
from feedview.models import  Like, Interested
from django.http import JsonResponse
from feedview.models import Comment


# --- HELPER FUNCTIONS ---

def check_level_compatibility(teacher_level, learner_level, category):
    """Check if teacher's level is appropriate for the learner"""
    if category == 'language':
        lang_levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
        if teacher_level in lang_levels and learner_level in lang_levels:
            teacher_idx = lang_levels.index(teacher_level)
            learner_idx = lang_levels.index(learner_level)
            return teacher_idx > learner_idx
    else:
        levels = ['Beginner', 'Intermediate', 'Advanced', 'Expert']
        if teacher_level in levels and learner_level in levels:
            teacher_idx = levels.index(teacher_level)
            learner_idx = levels.index(learner_level)
            return teacher_idx >= learner_idx
    return False


def calculate_enhanced_match_score(my_profile, other_profile):
    """Calculate match score using UserSkill model with proficiency levels"""
    my_teach_skills = my_profile.skills.filter(skill_type='teach')
    my_learn_skills = my_profile.skills.filter(skill_type='learn')
    other_teach_skills = other_profile.skills.filter(skill_type='teach')
    other_learn_skills = other_profile.skills.filter(skill_type='learn')
    
    direct_matches = []
    total_score = 0
    max_possible_score = len(my_teach_skills) + len(my_learn_skills)
    
    if max_possible_score == 0:
        return 0, []
    
    # You teach -> They learn
    for my_teach in my_teach_skills:
        for other_learn in other_learn_skills:
            if my_teach.skill_name.lower() == other_learn.skill_name.lower():
                level_compatible = check_level_compatibility(
                    my_teach.proficiency_level, other_learn.proficiency_level, my_teach.category
                )
                total_score += 15 if level_compatible else 10
                direct_matches.append({
                    'skill_name': my_teach.skill_name,
                    'type': 'You teach → They learn',
                    'level_compatible': level_compatible
                })
    
    # They teach -> You learn
    for my_learn in my_learn_skills:
        for other_teach in other_teach_skills:
            if my_learn.skill_name.lower() == other_teach.skill_name.lower():
                level_compatible = check_level_compatibility(
                    other_teach.proficiency_level, my_learn.proficiency_level, other_teach.category
                )
                total_score += 15 if level_compatible else 10
                direct_matches.append({
                    'skill_name': my_learn.skill_name,
                    'type': 'They teach → You learn',
                    'level_compatible': level_compatible
                })
    
    percentage = int((total_score / (max_possible_score * 15)) * 100) if max_possible_score > 0 else 0
    return min(percentage, 100), direct_matches


def calculate_match_percentage(my_teach, my_learn, other_teach, other_learn):
    """Legacy match calculation for backward compatibility"""
    my_teach_set = {skill.lower().strip() for skill in my_teach}
    my_learn_set = {skill.lower().strip() for skill in my_learn}
    other_teach_set = {skill.lower().strip() for skill in other_teach}
    other_learn_set = {skill.lower().strip() for skill in other_learn}
    
    match_count = len(my_learn_set & other_teach_set) + len(my_teach_set & other_learn_set)
    total_skills = len(my_teach_set) + len(my_learn_set)
    return int((match_count / total_skills) * 100) if total_skills > 0 else 0


# --- VIEW FUNCTIONS ---

@login_required
def view_other_profile(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    other_profile, _ = UserProfile.objects.get_or_create(user=other_user)

    current_user = request.user
    current_profile, _ = UserProfile.objects.get_or_create(user=current_user)

    is_own_profile = current_user == other_user

    # ====================
    # GET SKILLS FROM UserSkill MODEL (NOT text fields)
    # ====================
    
    # Get other user's skills from UserSkill model
    other_teach_skills_qs = other_profile.skills.filter(skill_type='teach')
    other_learn_skills_qs = other_profile.skills.filter(skill_type='learn')
    
    # Get current user's skills from UserSkill model
    current_teach_skills_qs = current_profile.skills.filter(skill_type='teach')
    current_learn_skills_qs = current_profile.skills.filter(skill_type='learn')
    
    # Convert to lists of skill names for display
    other_teach_skills = [skill.skill_name for skill in other_teach_skills_qs]
    other_learn_skills = [skill.skill_name for skill in other_learn_skills_qs]
    
    # Calculate enhanced match score using UserSkill model
    match_score, match_details = calculate_enhanced_match_score(current_profile, other_profile)
    
    # If no skills in UserSkill model, fall back to legacy text fields
    if match_score == 0:
        # Fallback to old text-based skills
        my_teach = current_profile.get_skills_to_teach_list()
        my_learn = current_profile.get_skills_to_learn_list()
        other_teach = other_profile.get_skills_to_teach_list()
        other_learn = other_profile.get_skills_to_learn_list()
        match_score = calculate_match_percentage(my_teach, my_learn, other_teach, other_learn)
        
        # If still no skills, use the querysets we already have
        if not other_teach:
            other_teach_skills = other_teach_skills
            other_learn_skills = other_learn_skills

    # ====================
    # MATCH REQUEST LOGIC
    # ====================

    is_connected = MatchRequest.objects.filter(
        sender=current_user,
        receiver=other_user,
        status='accepted'
    ).exists() or MatchRequest.objects.filter(
        sender=other_user,
        receiver=current_user,
        status='accepted'
    ).exists()

    request_sent = MatchRequest.objects.filter(
        sender=current_user,
        receiver=other_user,
        status='pending'
    ).exists()

    received_request = MatchRequest.objects.filter(
        sender=other_user,
        receiver=current_user,
        status='pending'
    ).first()

    request_received = received_request is not None
    request_received_id = received_request.id if received_request else None

    certifications = Certification.objects.filter(
        user_profile=other_profile
    )
     # Reviews
    reviews = Review.objects.filter(
    reviewed_user=other_user
    ).order_by('-created_at')

    avg_rating = reviews.aggregate(
    Avg('rating')
    )['rating__avg']
    posts = Post.objects.filter(
    user=other_user
    ).order_by('-created_at')
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
        'other_user': other_user,
        'other_profile': other_profile,
        'match_score': match_score,
        'teach_skills': other_teach_skills,  # Now using UserSkill model
        'learn_skills': other_learn_skills,  # Now using UserSkill model
        'certifications': certifications,

        'is_own_profile': is_own_profile,
        'is_connected': is_connected,
        'request_sent': request_sent,
        'request_received': request_received,
        'request_received_id': request_received_id,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'posts': posts,
    }

    return render(request, 'profiles/view_other_profile.html', context)


@login_required
def send_connection_request(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    if request.user == other_user:
        messages.warning(request, "You cannot connect with yourself.")
        return redirect('dashboard_home')

    existing = MatchRequest.objects.filter(
        sender=request.user,
        receiver=other_user
    ).first()

    reverse_existing = MatchRequest.objects.filter(
        sender=other_user,
        receiver=request.user
    ).first()

    # already friends
    if existing and existing.status == 'accepted':
        messages.info(request, "Already friends.")
        return redirect('view_other_profile', user_id=user_id)

    if reverse_existing and reverse_existing.status == 'accepted':
        messages.info(request, "Already friends.")
        return redirect('view_other_profile', user_id=user_id)

    # pending request exists
    if existing and existing.status == 'pending':
        messages.info(request, "Request already sent.")
        return redirect('view_other_profile', user_id=user_id)

    if reverse_existing and reverse_existing.status == 'pending':
        messages.info(request, "This user already sent you a request.")
        return redirect('view_other_profile', user_id=user_id)

    # reuse old declined request
    if existing:
        existing.status = 'pending'
        existing.save()
    else:
        MatchRequest.objects.create(
            sender=request.user,
            receiver=other_user,
            status='pending'
        )

    messages.success(request, "Request sent.")
    return redirect('view_other_profile', user_id=user_id)


@login_required
def accept_connection(request, request_id):
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

    return redirect('view_other_profile', user_id=req.sender.id)


@login_required
def unfriend_user(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    # Find accepted friendship/match
    friendship = MatchRequest.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user),
        status='accepted'
    ).first()

    if friendship:
        friendship.delete()

        # get profiles
        sender_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        receiver_profile, _ = UserProfile.objects.get_or_create(user=other_user)

        # decrease count safely
        sender_profile.study_partners_count = max(
            0, sender_profile.study_partners_count - 1
        )
        receiver_profile.study_partners_count = max(
            0, receiver_profile.study_partners_count - 1
        )

        sender_profile.save()
        receiver_profile.save()

    return redirect('view_other_profile', user_id=user_id)


@login_required
def block_user(request, user_id):
    messages.success(request, "User blocked.")
    return redirect('dashboard_home')


@login_required
def decline_connection(request, request_id):
    req = get_object_or_404(
        MatchRequest,
        id=request_id,
        receiver=request.user
    )
    
    req.status = 'declined'
    req.save()
    
    return redirect('view_other_profile', user_id=req.sender.id)


@login_required
def cancel_request(request, user_id):
    MatchRequest.objects.filter(
        sender=request.user,
        receiver_id=user_id,
        status='pending'
    ).delete()

    return redirect('view_other_profile', user_id=user_id)