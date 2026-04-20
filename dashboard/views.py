# dashboard/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from useraccount.models import UserProfile
from datetime import datetime
import json
def calculate_match_score(my_teach, my_learn, other_teach, other_learn):
    """
    Calculate match score between two users
    Returns score from 0-100
    """
    score = 0
    max_score = 0
    
    # User A teaches what User B wants to learn
    for teach in my_teach:
        for learn in other_learn:
            max_score += 2
            if teach.lower() == learn.lower():
                score += 2
            elif teach.lower() in learn.lower() or learn.lower() in teach.lower():
                score += 1
    
    # User B teaches what User A wants to learn
    for teach in other_teach:
        for learn in my_learn:
            max_score += 2
            if teach.lower() == learn.lower():
                score += 2
            elif teach.lower() in learn.lower() or learn.lower() in teach.lower():
                score += 1
    
    if max_score == 0:
        return 0
    
    return int((score / max_score) * 100)


@login_required
def dashboard_home(request):
    # Get current user's profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get current user's skills as lists
    my_teach = profile.get_skills_to_teach_list()
    my_learn = profile.get_skills_to_learn_list()
    
    # If user has no skills, show empty matches
    if not my_teach and not my_learn:
        matches = []
    else:
        # Get all other users
        other_profiles = UserProfile.objects.exclude(user=request.user)
        
        # Calculate matches with scores
        match_list = []
        
        for other in other_profiles:
            other_teach = other.get_skills_to_teach_list()
            other_learn = other.get_skills_to_learn_list()
            
            # Only consider if there's potential match
            if my_teach and other_learn:  # I teach what they learn
                score = calculate_match_score(my_teach, my_learn, other_teach, other_learn)
                
                if score > 0:
                    # Find common skills for display
                    common_teach_to_learn = []
                    for teach in my_teach:
                        for learn in other_learn:
                            if teach.lower() == learn.lower():
                                common_teach_to_learn.append(teach)
                    
                    common_learn_from_teach = []
                    for teach in other_teach:
                        for learn in my_learn:
                            if teach.lower() == learn.lower():
                                common_learn_from_teach.append(teach)
                    
                    match_list.append({
                        'name': other.user.username,
                        'skill_offer': common_teach_to_learn[0] if common_teach_to_learn else (other_teach[0] if other_teach else 'Various'),
                        'skill_want': common_learn_from_teach[0] if common_learn_from_teach else (my_learn[0] if my_learn else 'Learning'),
                        'score': score,
                        'profile_id': other.id,
                        'user_id': other.user.id,
                        'common_teach': common_teach_to_learn,
                        'common_learn': common_learn_from_teach
                    })
        
        # Sort by score (highest first) and take top 5
        match_list.sort(key=lambda x: x['score'], reverse=True)
        matches = match_list[:5]
    
    # Study feed (for Feed tab)
    study_feed = []
    
    # Get recent matches as feed items
    for match in matches[:3]:
        study_feed.append({
            'user': match['name'],
            'action': f"matched with you for {match['skill_offer']} → {match['skill_want']}",
            'time_ago': 'Just now',
            'topic': match['skill_offer'],
            'goal': match['skill_want'],
            'likes': 0,
            'comments': 0
        })
    
    # Add some sample feed items if empty
    if not study_feed:
        study_feed = [
            {
                'user': 'StudyBuddy',
                'action': 'posted: Looking for Python study partner',
                'time_ago': '2 hours ago',
                'topic': 'Python',
                'goal': 'Django',
                'likes': 3,
                'comments': 1
            },
        ]
    
    # User activities (for Activity tab)
    user_activities = []
    
    # Add pending match requests here (you'll implement Request model later)
    if matches:
        user_activities.append({
            'icon': 'person-plus', 
            'message': f'You have {len(matches)} new match suggestions', 
            'date': 'Today'
        })
    
    if profile.updated_at:
        user_activities.append({
            'icon': 'pencil', 
            'message': 'Profile updated', 
            'date': 'Recently'
        })
    
    # If no activities, show placeholder
    if not user_activities:
        user_activities.append({
            'icon': 'inbox',
            'message': 'No recent activity',
            'date': ''
        })
    
    # Calculate stats
    weekly_hours = 0
    sessions_done = 0
    
    def get_time_of_day():
        hour = datetime.now().hour
        if hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        else:
            return "evening"
    
    context = {
        'profile': profile,
        'matches': matches,
        'study_feed': study_feed,
        'user_activities': user_activities,
        'weekly_hours': weekly_hours,
        'sessions_done': sessions_done,
        'streak_days': getattr(request.user, 'streak_days', 5),
        'consistency_percent': 75,
        'sql_progress': 65,
        'figma_progress': 40,
        'python_progress': 80,
        'time_of_day': get_time_of_day(),
        'matches_json': json.dumps(matches), 
        'today': datetime.now(),
    }
    # At the bottom of dashboard_home function, before return, add:
    print(f"DEBUG: Found {len(matches)} matches")
    for m in matches:
        print(f"  - {m['name']}: {m['score']}%")
    return render(request, 'dashboard/index.html', context)