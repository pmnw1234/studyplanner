# profiles/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from useraccount.models import UserProfile

@login_required
def view_other_profile(request, user_id):
    """View another user's profile"""
    
    # Get the other user
    other_user = get_object_or_404(User, id=user_id)
    other_profile = other_user.userprofile
    
    # Get current user's profile for match calculation
    current_profile = request.user.userprofile
    
    # Calculate match score
    my_teach = set(current_profile.get_skills_to_teach_list())
    my_learn = set(current_profile.get_skills_to_learn_list())
    other_teach = set(other_profile.get_skills_to_teach_list())
    other_learn = set(other_profile.get_skills_to_learn_list())
    
    match_score = 0
    total = 0
    
    for teach in my_teach:
        for learn in other_learn:
            total += 1
            if teach.lower() == learn.lower():
                match_score += 1
                
    for teach in other_teach:
        for learn in my_learn:
            total += 1
            if teach.lower() == learn.lower():
                match_score += 1
    
    match_percentage = int((match_score / total) * 100) if total > 0 else 0
    
    context = {
        'other_user': other_user,
        'other_profile': other_profile,
        'match_score': match_percentage,
        'teach_skills': other_profile.get_skills_to_teach_list(),
        'learn_skills': other_profile.get_skills_to_learn_list(),
    }
    
    return render(request, 'profiles/view_other_profile.html', context)


# profiles/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from useraccount.models import UserProfile, ConnectionRequest, Connection

@login_required
def view_other_profile(request, user_id):
    """View another user's profile"""
    
    other_user = get_object_or_404(User, id=user_id)
    other_profile = other_user.userprofile
    current_user = request.user
    
    # Check if already connected
    is_connected = Connection.objects.filter(
        user1=current_user, user2=other_user
    ).exists() or Connection.objects.filter(
        user1=other_user, user2=current_user
    ).exists()
    
    # Check if request already sent
    request_sent = ConnectionRequest.objects.filter(
        from_user=current_user, to_user=other_user, status='pending'
    ).exists()
    
    # Check if request received
    request_received = ConnectionRequest.objects.filter(
        from_user=other_user, to_user=current_user, status='pending'
    ).exists()
    
    # Calculate match score
    current_profile = current_user.userprofile
    my_teach = set(current_profile.get_skills_to_teach_list())
    my_learn = set(current_profile.get_skills_to_learn_list())
    other_teach = set(other_profile.get_skills_to_teach_list())
    other_learn = set(other_profile.get_skills_to_learn_list())
    
    match_score = 0
    total = 0
    
    for teach in my_teach:
        for learn in other_learn:
            total += 1
            if teach.lower() == learn.lower():
                match_score += 1
                
    for teach in other_teach:
        for learn in my_learn:
            total += 1
            if teach.lower() == learn.lower():
                match_score += 1
    
    match_percentage = int((match_score / total) * 100) if total > 0 else 0
    
    context = {
        'other_user': other_user,
        'other_profile': other_profile,
        'match_score': match_percentage,
        'teach_skills': other_profile.get_skills_to_teach_list(),
        'learn_skills': other_profile.get_skills_to_learn_list(),
        'is_connected': is_connected,
        'request_sent': request_sent,
        'request_received': request_received,
    }
    
    return render(request, 'profiles/view_other_profile.html', context)


@login_required
def send_connection_request(request, user_id):
    """Send a connection request to another user"""
    
    to_user = get_object_or_404(User, id=user_id)
    from_user = request.user
    
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
    Connection.objects.create(
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
    
    return redirect('view_other_profile', user_id=user_id)