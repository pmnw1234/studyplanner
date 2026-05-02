# profiles/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
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


@login_required
def send_connection_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    if request.user == to_user:
        messages.warning(request, "You cannot connect with yourself!")
        return redirect('dashboard_home')
    
    ConnectionRequest.objects.get_or_create(from_user=request.user, to_user=to_user, status='pending')
    messages.success(request, f"Request sent to {to_user.username}!")
    return redirect('view_other_profile', user_id=user_id)


@login_required
def accept_connection(request, request_id):
    conn_req = get_object_or_404(ConnectionRequest, id=request_id, to_user=request.user, status='pending')
    Connection.objects.get_or_create(user1=conn_req.from_user, user2=conn_req.to_user)
    conn_req.status = 'accepted'
    conn_req.save()
    messages.success(request, f"Connected with {conn_req.from_user.username}!")
    return redirect('dashboard_home')


@login_required
def decline_connection(request, request_id):
    conn_req = get_object_or_404(ConnectionRequest, id=request_id, to_user=request.user, status='pending')
    conn_req.status = 'declined'
    conn_req.save()
    return redirect('dashboard_home')


@login_required
def cancel_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    ConnectionRequest.objects.filter(from_user=request.user, to_user=to_user, status='pending').delete()
    return redirect('view_other_profile', user_id=user_id)