# profiles/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from useraccount.models import UserProfile, Connection, ConnectionRequest
from feedview.models import MatchRequest
from useraccount.models import UserProfile, UserSkill, ConnectionRequest, Connection

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

    my_teach = current_profile.get_skills_to_teach_list()
    my_learn = current_profile.get_skills_to_learn_list()
    other_teach = other_profile.get_skills_to_teach_list()
    other_learn = other_profile.get_skills_to_learn_list()

    match_score = calculate_match_percentage(
        my_teach,
        my_learn,
        other_teach,
        other_learn
    )

    # already friends = accepted match request exists
    is_connected = MatchRequest.objects.filter(
        sender=current_user,
        receiver=other_user,
        status='accepted'
    ).exists() or MatchRequest.objects.filter(
        sender=other_user,
        receiver=current_user,
        status='accepted'
    ).exists()

    # request sent by me
    request_sent = MatchRequest.objects.filter(
        sender=current_user,
        receiver=other_user,
        status='pending'
    ).exists()

    # request received from them
    received_request = MatchRequest.objects.filter(
        sender=other_user,
        receiver=current_user,
        status='pending'
    ).first()

    request_received = received_request is not None
    request_received_id = received_request.id if received_request else None

    current_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    # Get skills
    my_teach_skills = current_profile.skills.filter(skill_type='teach')
    my_learn_skills = current_profile.skills.filter(skill_type='learn')
    other_teach_skills = other_profile.skills.filter(skill_type='teach')
    other_learn_skills = other_profile.skills.filter(skill_type='learn')
    
    # Calculate Scores
    enhanced_score, direct_matches = calculate_enhanced_match_score(current_profile, other_profile)
    
    # Check connection status
    is_connected = Connection.objects.filter(user1=request.user, user2=other_user).exists() or \
                   Connection.objects.filter(user1=other_user, user2=request.user).exists()
    
    request_sent = ConnectionRequest.objects.filter(from_user=request.user, to_user=other_user, status='pending').exists()
    received_req = ConnectionRequest.objects.filter(from_user=other_user, to_user=request.user, status='pending').first()


    context = {
        'other_user': other_user,
        'other_profile': other_profile,
        'match_score': match_score,
        'teach_skills': other_teach,
        'learn_skills': other_learn,
        'is_own_profile': is_own_profile,
        'match_score': enhanced_score,
        'is_connected': is_connected,
        'request_sent': request_sent,
        'request_received': received_req is not None,
        'request_received_id': received_req.id if received_req else None,
        'direct_matches': direct_matches,
        'teach_skills': other_teach_skills,
        'learn_skills': other_learn_skills,
        'certifications': other_profile.certifications.all(),
    }
    return render(request, 'profiles/view_other_profile.html', context)


# @login_required
# def send_connection_request(request, user_id):
#     """Send a connection request to another user"""
    
#     to_user = get_object_or_404(User, id=user_id)
#     from_user = request.user
    
#     # Don't send request to yourself
#     if from_user == to_user:
#         messages.warning(request, "You cannot send a connection request to yourself!")
#         return redirect('dashboard_home')
    
#     # Ensure profile exists for both users
#     UserProfile.objects.get_or_create(user=to_user)
#     UserProfile.objects.get_or_create(user=from_user)
    
#     # Check if already connected
#     if Connection.objects.filter(
#         user1=from_user, user2=to_user
#     ).exists() or Connection.objects.filter(
#         user1=to_user, user2=from_user
#     ).exists():
#         messages.warning(request, f"You are already connected with {to_user.username}!")
#         return redirect('view_other_profile', user_id=user_id)
    
#     # Check if request already exists
#     existing_request = ConnectionRequest.objects.filter(
#         from_user=from_user, to_user=to_user, status='pending'
#     ).exists()
    
#     if existing_request:
#         messages.warning(request, f"Request already sent to {to_user.username}!")
#         return redirect('view_other_profile', user_id=user_id)
    
#     # Create new request
#     ConnectionRequest.objects.create(
#         from_user=from_user,
#         to_user=to_user,
#         status='pending'
#     )
    
#     messages.success(request, f"Connection request sent to {to_user.username}!")
#     return redirect('view_other_profile', user_id=user_id)

@login_required
def send_connection_request(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    if request.user == other_user:
        return redirect('view_other_profile', user_id=user_id)

    # check existing request both directions
    existing = MatchRequest.objects.filter(
        sender=request.user,
        receiver=other_user
    ).first()

    reverse_existing = MatchRequest.objects.filter(
        sender=other_user,
        receiver=request.user
    ).first()

    # already sent by me
    if existing:
        if existing.status == 'pending':
            return redirect('view_other_profile', user_id=user_id)

        elif existing.status == 'declined':
            existing.status = 'pending'
            existing.save()
            return redirect('view_other_profile', user_id=user_id)

        elif existing.status == 'accepted':
            return redirect('view_other_profile', user_id=user_id)

    # already sent by them
    if reverse_existing:
        return redirect('view_other_profile', user_id=user_id)

    # create new request
    MatchRequest.objects.create(
        sender=request.user,
        receiver=other_user,
        status='pending'
    )

    to_user = get_object_or_404(User, id=user_id)
    if request.user == to_user:
        messages.warning(request, "You cannot connect with yourself!")
        return redirect('dashboard_home')
    
    ConnectionRequest.objects.get_or_create(from_user=request.user, to_user=to_user, status='pending')
    messages.success(request, f"Request sent to {to_user.username}!")
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
# @login_required
# def accept_connection(request, request_id):
#     """Accept a connection request"""
    
#     connection_request = get_object_or_404(ConnectionRequest, id=request_id, to_user=request.user, status='pending')
    
#     # Create connection
#     Connection.objects.get_or_create(
#         user1=connection_request.from_user,
#         user2=connection_request.to_user
#     )
    
#     # Update request status
#     connection_request.status = 'accepted'
#     connection_request.save()
    
#     messages.success(request, f"You are now connected with {connection_request.from_user.username}!")
#     return redirect('dashboard_home')

    # conn_req = get_object_or_404(ConnectionRequest, id=request_id, to_user=request.user, status='pending')
    # Connection.objects.get_or_create(user1=conn_req.from_user, user2=conn_req.to_user)
    # conn_req.status = 'accepted'
    # conn_req.save()
    # messages.success(request, f"Connected with {conn_req.from_user.username}!")
    # return redirect('dashboard_home')



# @login_required
# def decline_connection(request, request_id):
#     """Decline a connection request"""
    
#     connection_request = get_object_or_404(ConnectionRequest, id=request_id, to_user=request.user, status='pending')
    
#     connection_request.status = 'declined'
#     connection_request.save()
    
#     messages.info(request, f"Connection request from {connection_request.from_user.username} declined.")
#     return redirect('dashboard_home')
@login_required
def decline_connection(request, request_id):

    req = get_object_or_404(
        MatchRequest,
        id=request_id,
        receiver=request.user
    )
    conn_req = get_object_or_404(ConnectionRequest, id=request_id, to_user=request.user, status='pending')
    conn_req.status = 'declined'
    conn_req.save()
    return redirect('dashboard_home')

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
# @login_required
# def cancel_request(request, user_id):
#     """Cancel a sent connection request"""
    
#     to_user = get_object_or_404(User, id=user_id)
#     connection_request = ConnectionRequest.objects.filter(
#         from_user=request.user, to_user=to_user, status='pending'
#     ).first()
    
#     if connection_request:
#         connection_request.delete()
#         messages.info(request, f"Connection request to {to_user.username} cancelled.")
#     else:
#         messages.warning(request, "No pending request found.")
    
#     return redirect('view_other_profile', user_id=user_id)
    # to_user = get_object_or_404(User, id=user_id)
    # ConnectionRequest.objects.filter(from_user=request.user, to_user=to_user, status='pending').delete()
    # return redirect('view_other_profile', user_id=user_id)
