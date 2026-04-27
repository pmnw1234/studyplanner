# profiles/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from useraccount.models import UserProfile, UserSkill, ConnectionRequest, Connection


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
    """
    Calculate enhanced match score using UserSkill model with proficiency levels
    """
    # Get skills from UserSkill model
    my_teach_skills = my_profile.skills.filter(skill_type='teach')
    my_learn_skills = my_profile.skills.filter(skill_type='learn')
    other_teach_skills = other_profile.skills.filter(skill_type='teach')
    other_learn_skills = other_profile.skills.filter(skill_type='learn')
    
    direct_matches = []
    total_score = 0
    max_possible_score = len(my_teach_skills) + len(my_learn_skills)
    
    if max_possible_score == 0:
        return 0, []
    
    # Check skills where current user can teach and other wants to learn
    for my_teach in my_teach_skills:
        for other_learn in other_learn_skills:
            if my_teach.skill_name.lower() == other_learn.skill_name.lower():
                level_compatible = check_level_compatibility(
                    my_teach.proficiency_level,
                    other_learn.proficiency_level,
                    my_teach.category
                )
                match_score = 15 if level_compatible else 10
                total_score += match_score
                
                direct_matches.append({
                    'skill_name': my_teach.skill_name,
                    'type': 'You teach → They learn',
                    'user_level': my_teach.proficiency_level,
                    'their_level': other_learn.proficiency_level,
                    'level_compatible': level_compatible,
                    'category': my_teach.category
                })
    
    # Check skills where other can teach and current user wants to learn
    for my_learn in my_learn_skills:
        for other_teach in other_teach_skills:
            if my_learn.skill_name.lower() == other_teach.skill_name.lower():
                level_compatible = check_level_compatibility(
                    other_teach.proficiency_level,
                    my_learn.proficiency_level,
                    other_teach.category
                )
                match_score = 15 if level_compatible else 10
                total_score += match_score
                
                direct_matches.append({
                    'skill_name': my_learn.skill_name,
                    'type': 'They teach → You learn',
                    'user_level': my_learn.proficiency_level,
                    'their_level': other_teach.proficiency_level,
                    'level_compatible': level_compatible,
                    'category': other_teach.category
                })
    
    # Calculate percentage score (max 100)
    if max_possible_score > 0:
        percentage = int((total_score / (max_possible_score * 15)) * 100)
        percentage = min(percentage, 100)
    else:
        percentage = 0
    
    return percentage, direct_matches


def calculate_match_percentage(my_teach, my_learn, other_teach, other_learn):
    """
    Legacy match percentage calculation (kept for compatibility)
    """
    my_teach_set = {skill.lower().strip() for skill in my_teach}
    my_learn_set = {skill.lower().strip() for skill in my_learn}
    other_teach_set = {skill.lower().strip() for skill in other_teach}
    other_learn_set = {skill.lower().strip() for skill in other_learn}
    
    they_can_teach_me = my_learn_set & other_teach_set
    i_can_teach_them = my_teach_set & other_learn_set
    
    total_skills = len(my_teach_set) + len(my_learn_set)
    
    if total_skills == 0:
        return 0
    
    match_count = len(they_can_teach_me) + len(i_can_teach_them)
    percentage = int((match_count / total_skills) * 100)
    
    return percentage


@login_required
def view_other_profile(request, user_id):
    """View another user's profile with enhanced skill data"""
    
    other_user = get_object_or_404(User, id=user_id)
    
    # Create profile if it doesn't exist
    other_profile, created = UserProfile.objects.get_or_create(user=other_user)
    
    current_user = request.user
    current_profile, created = UserProfile.objects.get_or_create(user=current_user)
    
    # Get skills from UserSkill model (with levels and categories)
    my_teach_skills = current_profile.skills.filter(skill_type='teach')
    my_learn_skills = current_profile.skills.filter(skill_type='learn')
    other_teach_skills = other_profile.skills.filter(skill_type='teach')
    other_learn_skills = other_profile.skills.filter(skill_type='learn')
    
    # Get certifications for other user
    other_certifications = other_profile.certifications.all()
    
    # Legacy lists for compatibility
    my_teach = [s.skill_name for s in my_teach_skills]
    my_learn = [s.skill_name for s in my_learn_skills]
    other_teach = [s.skill_name for s in other_teach_skills]
    other_learn = [s.skill_name for s in other_learn_skills]
    
    # Prepare skills with levels and categories for template
    teach_skills_data = [
        {'name': skill.skill_name, 'level': skill.proficiency_level, 'category': skill.category}
        for skill in other_teach_skills
    ]
    learn_skills_data = [
        {'name': skill.skill_name, 'level': skill.proficiency_level, 'category': skill.category}
        for skill in other_learn_skills
    ]
    
    # Calculate enhanced match score
    enhanced_score, direct_matches = calculate_enhanced_match_score(current_profile, other_profile)
    
    # Also calculate legacy score for comparison
    legacy_score = calculate_match_percentage(my_teach, my_learn, other_teach, other_learn)
    
    # Use enhanced score as primary
    match_percentage = enhanced_score
    
    # Check connection status
    is_connected = Connection.objects.filter(
        user1=current_user, user2=other_user
    ).exists() or Connection.objects.filter(
        user1=other_user, user2=current_user
    ).exists()
    
    # Check if request already sent by current user
    request_sent = ConnectionRequest.objects.filter(
        from_user=current_user, to_user=other_user, status='pending'
    ).exists()
    
    # Check if request received from other user
    received_request = ConnectionRequest.objects.filter(
        from_user=other_user, to_user=current_user, status='pending'
    ).first()
    request_received = received_request is not None
    request_received_id = received_request.id if received_request else None
    
    # Calculate matches for display
    my_teach_set = {s.lower().strip() for s in my_teach}
    my_learn_set = {s.lower().strip() for s in my_learn}
    other_teach_set = {s.lower().strip() for s in other_teach}
    other_learn_set = {s.lower().strip() for s in other_learn}
    
    they_can_teach_me = list(my_learn_set & other_teach_set)
    i_can_teach_them = list(my_teach_set & other_learn_set)
    
    # Determine match strength
    if match_percentage >= 70:
        match_strength = 'strong'
    elif match_percentage >= 40:
        match_strength = 'medium'
    else:
        match_strength = 'weak'
    
    # Debug output
    print(f"\n{'='*50}")
    print(f"📊 MATCH CALCULATION: {current_user.username} vs {other_user.username}")
    print(f"{'='*50}")
    print(f"You teach: {[(s.skill_name, s.proficiency_level) for s in my_teach_skills]}")
    print(f"You learn: {[(s.skill_name, s.proficiency_level) for s in my_learn_skills]}")
    print(f"Their teach: {[(s.skill_name, s.proficiency_level) for s in other_teach_skills]}")
    print(f"Their learn: {[(s.skill_name, s.proficiency_level) for s in other_learn_skills]}")
    print(f"\n✅ They can teach you: {they_can_teach_me}")
    print(f"✅ You can teach them: {i_can_teach_them}")
    print(f"🎯 Enhanced Match Score: {match_percentage}%")
    print(f"📊 Legacy Score: {legacy_score}%")
    print(f"💪 Match Strength: {match_strength}")
    print(f"{'='*50}\n")
    
    context = {
        'other_user': other_user,
        'other_profile': other_profile,
        'match_score': match_percentage,
        'match_strength': match_strength,
        'teach_skills': teach_skills_data,  # Now includes level and category
        'learn_skills': learn_skills_data,  # Now includes level and category
        'teach_skills_list': other_teach,   # Backward compatibility
        'learn_skills_list': other_learn,   # Backward compatibility
        'is_connected': is_connected,
        'request_sent': request_sent,
        'request_received': request_received,
        'request_received_id': request_received_id,
        'direct_matches': direct_matches,
        'they_can_teach_me': they_can_teach_me,
        'i_can_teach_them': i_can_teach_them,
        'certifications': other_certifications,  # Add this line
    }
    
    return render(request, 'profiles/view_other_profile.html', context)

@login_required
def send_connection_request(request, user_id):
    """Send a connection request to another user"""
    
    to_user = get_object_or_404(User, id=user_id)
    from_user = request.user
    
    # Don't send request to yourself
    if from_user == to_user:
        messages.warning(request, "You cannot send a connection request to yourself!")
        return redirect('dashboard_home')
    
    # Ensure profile exists for both users
    UserProfile.objects.get_or_create(user=to_user)
    UserProfile.objects.get_or_create(user=from_user)
    
    # Check if already connected
    if Connection.objects.filter(
        user1=from_user, user2=to_user
    ).exists() or Connection.objects.filter(
        user1=to_user, user2=from_user
    ).exists():
        messages.warning(request, f"You are already connected with {to_user.username}!")
        return redirect('view_other_profile', user_id=user_id)
    
    # Check if request already exists
    existing_request = ConnectionRequest.objects.filter(
        from_user=from_user, to_user=to_user, status='pending'
    ).exists()
    
    if existing_request:
        messages.warning(request, f"Request already sent to {to_user.username}!")
        return redirect('view_other_profile', user_id=user_id)
    
    # Create new request
    ConnectionRequest.objects.create(
        from_user=from_user,
        to_user=to_user,
        status='pending'
    )
    
    messages.success(request, f"Connection request sent to {to_user.username}!")
    return redirect('view_other_profile', user_id=user_id)


@login_required
def accept_connection(request, request_id):
    """Accept a connection request"""
    
    connection_request = get_object_or_404(ConnectionRequest, id=request_id, to_user=request.user, status='pending')
    
    # Create connection
    Connection.objects.get_or_create(
        user1=connection_request.from_user,
        user2=connection_request.to_user
    )
    
    # Update request status
    connection_request.status = 'accepted'
    connection_request.save()
    
    messages.success(request, f"You are now connected with {connection_request.from_user.username}!")
    return redirect('dashboard_home')


@login_required
def decline_connection(request, request_id):
    """Decline a connection request"""
    
    connection_request = get_object_or_404(ConnectionRequest, id=request_id, to_user=request.user, status='pending')
    
    connection_request.status = 'declined'
    connection_request.save()
    
    messages.info(request, f"Connection request from {connection_request.from_user.username} declined.")
    return redirect('dashboard_home')


@login_required
def cancel_request(request, user_id):
    """Cancel a sent connection request"""
    
    to_user = get_object_or_404(User, id=user_id)
    connection_request = ConnectionRequest.objects.filter(
        from_user=request.user, to_user=to_user, status='pending'
    ).first()
    
    if connection_request:
        connection_request.delete()
        messages.info(request, f"Connection request to {to_user.username} cancelled.")
    else:
        messages.warning(request, "No pending request found.")
    
    return redirect('view_other_profile', user_id=user_id)