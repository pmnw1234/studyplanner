# profiles/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Avg

from useraccount.models import UserProfile
from feedview.models import MatchRequest
from reviews.models import Review


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def check_level_compatibility(teacher_level, learner_level, category):

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
                    my_teach.proficiency_level,
                    other_learn.proficiency_level,
                    my_teach.category
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
                    other_teach.proficiency_level,
                    my_learn.proficiency_level,
                    other_teach.category
                )

                total_score += 15 if level_compatible else 10

                direct_matches.append({
                    'skill_name': my_learn.skill_name,
                    'type': 'They teach → You learn',
                    'level_compatible': level_compatible
                })

    percentage = int((total_score / (max_possible_score * 15)) * 100)

    return min(percentage, 100), direct_matches


# =========================================================
# PROFILE VIEW
# =========================================================

@login_required
def view_other_profile(request, user_id):

    other_user = get_object_or_404(User, id=user_id)

    other_profile, _ = UserProfile.objects.get_or_create(
        user=other_user
    )

    current_profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    is_own_profile = request.user == other_user

    # Skills
    other_teach_skills = other_profile.skills.filter(skill_type='teach')
    other_learn_skills = other_profile.skills.filter(skill_type='learn')

    # Match score
    enhanced_score, direct_matches = calculate_enhanced_match_score(
        current_profile,
        other_profile
    )

    # Connection status
    is_connected = MatchRequest.objects.filter(
        sender=request.user,
        receiver=other_user,
        status='accepted'
    ).exists() or MatchRequest.objects.filter(
        sender=other_user,
        receiver=request.user,
        status='accepted'
    ).exists()

    # Request sent
    request_sent = MatchRequest.objects.filter(
        sender=request.user,
        receiver=other_user,
        status='pending'
    ).exists()

    # Request received
    received_request = MatchRequest.objects.filter(
        sender=other_user,
        receiver=request.user,
        status='pending'
    ).first()

    request_received = received_request is not None

    request_received_id = (
        received_request.id if received_request else None
    )

    # Reviews
    reviews = Review.objects.filter(
        reviewed_user=other_user
    ).order_by('-created_at')

    avg_rating = reviews.aggregate(
        Avg('rating')
    )['rating__avg']

    context = {
        'other_user': other_user,
        'other_profile': other_profile,

        'is_own_profile': is_own_profile,

        'is_connected': is_connected,

        'request_sent': request_sent,

        'request_received': request_received,

        'request_received_id': request_received_id,

        'match_score': enhanced_score,

        'direct_matches': direct_matches,

        'teach_skills': other_teach_skills,

        'learn_skills': other_learn_skills,

        'certifications': other_profile.certifications.all(),

        'reviews': reviews,

        'avg_rating': avg_rating,
    }

    return render(
        request,
        'profiles/view_other_profile.html',
        context
    )


# =========================================================
# SEND CONNECTION REQUEST
# =========================================================

@login_required
def send_connection_request(request, user_id):

    other_user = get_object_or_404(User, id=user_id)

    if request.user == other_user:
        return redirect('view_other_profile', user_id=user_id)

    existing = MatchRequest.objects.filter(
        sender=request.user,
        receiver=other_user
    ).first()

    reverse_existing = MatchRequest.objects.filter(
        sender=other_user,
        receiver=request.user
    ).first()

    # already sent
    if existing:

        if existing.status == 'pending':
            return redirect('view_other_profile', user_id=user_id)

        elif existing.status == 'declined':
            existing.status = 'pending'
            existing.save()

            return redirect('view_other_profile', user_id=user_id)

        elif existing.status == 'accepted':
            return redirect('view_other_profile', user_id=user_id)

    # already received
    if reverse_existing:
        return redirect('view_other_profile', user_id=user_id)

    MatchRequest.objects.create(
        sender=request.user,
        receiver=other_user,
        status='pending'
    )

    messages.success(
        request,
        f"Request sent to {other_user.username}!"
    )

    return redirect('view_other_profile', user_id=user_id)


# =========================================================
# ACCEPT CONNECTION
# =========================================================

@login_required
def accept_connection(request, request_id):

    req = get_object_or_404(
        MatchRequest,
        id=request_id,
        receiver=request.user
    )

    req.status = 'accepted'
    req.save()

    sender_profile, _ = UserProfile.objects.get_or_create(
        user=req.sender
    )

    receiver_profile, _ = UserProfile.objects.get_or_create(
        user=req.receiver
    )

    sender_profile.study_partners_count += 1
    receiver_profile.study_partners_count += 1

    sender_profile.save()
    receiver_profile.save()

    return redirect(
        'view_other_profile',
        user_id=req.sender.id
    )


# =========================================================
# DECLINE CONNECTION
# =========================================================

@login_required
def decline_connection(request, request_id):

    req = get_object_or_404(
        MatchRequest,
        id=request_id,
        receiver=request.user
    )

    req.status = 'declined'
    req.save()

    return redirect(
        'view_other_profile',
        user_id=req.sender.id
    )


# =========================================================
# CANCEL REQUEST
# =========================================================

@login_required
def cancel_request(request, user_id):

    MatchRequest.objects.filter(
        sender=request.user,
        receiver_id=user_id,
        status='pending'
    ).delete()

    return redirect(
        'view_other_profile',
        user_id=user_id
    )