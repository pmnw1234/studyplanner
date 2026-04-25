# profiles/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from useraccount.models import UserProfile, ConnectionRequest, Connection


def calculate_match_percentage(my_teach, my_learn, other_teach, other_learn):
    """
    Calculate match percentage between two users
    Simple and accurate calculation
    """
    # Convert to lowercase sets for comparison
    my_teach_set = {skill.lower().strip() for skill in my_teach}
    my_learn_set = {skill.lower().strip() for skill in my_learn}
    other_teach_set = {skill.lower().strip() for skill in other_teach}
    other_learn_set = {skill.lower().strip() for skill in other_learn}
    
    # Find matches
    they_can_teach_me = my_learn_set & other_teach_set  # What I want to learn, they teach
    i_can_teach_them = my_teach_set & other_learn_set  # What I teach, they want to learn
    
    # Calculate total possible matches
    total_skills = len(my_teach_set) + len(my_learn_set)
    
    if total_skills == 0:
        return 0
    
    # Calculate match count and percentage
    match_count = len(they_can_teach_me) + len(i_can_teach_them)
    percentage = int((match_count / total_skills) * 100)
    
    return percentage


@login_required
def view_other_profile(request, user_id):
    """View another user's profile"""
    
    other_user = get_object_or_404(User, id=user_id)
    
    # Create profile if it doesn't exist
    other_profile, created = UserProfile.objects.get_or_create(user=other_user)
    
    current_user = request.user
    current_profile, created = UserProfile.objects.get_or_create(user=current_user)
    
    # Get skills as lists
    my_teach = current_profile.get_skills_to_teach_list()
    my_learn = current_profile.get_skills_to_learn_list()
    other_teach = other_profile.get_skills_to_teach_list()
    other_learn = other_profile.get_skills_to_learn_list()
    
    # Calculate match score using the new function
    match_percentage = calculate_match_percentage(my_teach, my_learn, other_teach, other_learn)
    
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
    
    # Debug output (will show in terminal)
    print(f"\n{'='*50}")
    print(f"📊 MATCH CALCULATION: {current_user.username} vs {other_user.username}")
    print(f"{'='*50}")
    print(f"You teach: {my_teach}")
    print(f"You learn: {my_learn}")
    print(f"Their teach: {other_teach}")
    print(f"Their learn: {other_learn}")
    
    # Calculate matches for display
    my_teach_set = {s.lower().strip() for s in my_teach}
    my_learn_set = {s.lower().strip() for s in my_learn}
    other_teach_set = {s.lower().strip() for s in other_teach}
    other_learn_set = {s.lower().strip() for s in other_learn}
    
    they_can_teach_me = list(my_learn_set & other_teach_set)
    i_can_teach_them = list(my_teach_set & other_learn_set)
    
    print(f"\n✅ They can teach you: {they_can_teach_me}")
    print(f"✅ You can teach them: {i_can_teach_them}")
    print(f"🎯 Match Score: {match_percentage}%")
    print(f"{'='*50}\n")
    
    context = {
        'other_user': other_user,
        'other_profile': other_profile,
        'match_score': match_percentage,
        'teach_skills': other_teach,
        'learn_skills': other_learn,
        'is_connected': is_connected,
        'request_sent': request_sent,
        'request_received': request_received,
        'request_received_id': request_received_id,
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