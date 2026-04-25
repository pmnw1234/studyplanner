# dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from useraccount.models import UserProfile
from feedview.models import MatchRequest
from django.utils.timesince import timesince
from datetime import datetime
import json

def calculate_match_score(my_teach, my_learn, other_teach, other_learn):
    """
    Simple and accurate match score calculation
    """
    # Convert to lowercase sets for comparison
    my_teach_set = {skill.lower().strip() for skill in my_teach}
    my_learn_set = {skill.lower().strip() for skill in my_learn}
    other_teach_set = {skill.lower().strip() for skill in other_teach}
    other_learn_set = {skill.lower().strip() for skill in other_learn}
    
    # Calculate matches
    they_can_teach_me = my_learn_set & other_teach_set  # What I want to learn, they teach
    i_can_teach_them = my_teach_set & other_learn_set  # What I teach, they want to learn
    
    # Calculate total possible matches
    total_skills = len(my_learn_set) + len(my_teach_set)
    
    if total_skills == 0:
        return 0
    
    # Each match is worth equal points
    match_score = len(they_can_teach_me) + len(i_can_teach_them)
    
    # Calculate percentage
    percentage = (match_score / total_skills) * 100
    
    return int(percentage)


@login_required
def dashboard_home(request):
    # Get current user's profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get current user's skills as lists
    my_teach = profile.get_skills_to_teach_list()
    my_learn = profile.get_skills_to_learn_list()
    
    # Debug output
    print(f"\n{'='*60}")
    print(f"🔍 DASHBOARD MATCHING FOR: {request.user.username}")
    print(f"{'='*60}")
    print(f"📚 You teach: {my_teach}")
    print(f"🎯 You want to learn: {my_learn}")
    print(f"{'='*60}\n")
    
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
            
            # Convert to sets for comparison
            my_teach_set = {skill.lower().strip() for skill in my_teach}
            my_learn_set = {skill.lower().strip() for skill in my_learn}
            other_teach_set = {skill.lower().strip() for skill in other_teach}
            other_learn_set = {skill.lower().strip() for skill in other_learn}
            
            # Find matches
            they_can_teach_me = list(my_learn_set & other_teach_set)
            i_can_teach_them = list(my_teach_set & other_learn_set)
            
            # Calculate score
            total_skills = len(my_learn_set) + len(my_teach_set)
            match_count = len(they_can_teach_me) + len(i_can_teach_them)
            
            if total_skills > 0:
                score = int((match_count / total_skills) * 100)
            else:
                score = 0
            
            if score > 0:
                # Determine what to display
                if they_can_teach_me:
                    display_skill = they_can_teach_me[0].capitalize()
                    display_message = f"can teach you {display_skill}"
                elif i_can_teach_them:
                    display_skill = i_can_teach_them[0].capitalize()
                    display_message = f"wants to learn {display_skill}"
                else:
                    display_skill = other_teach[0] if other_teach else "Skills"
                    display_message = "has skills to share"
                
                match_list.append({
                    'name': other.user.username,
                    'skill_offer': display_skill,
                    'skill_want': display_message,
                    'score': score,
                    'profile_id': other.id,
                    'user_id': other.user.id,
                    'common_teach': i_can_teach_them,
                    'common_learn': they_can_teach_me,
                    'profile_picture': other.profile_picture.url if other.profile_picture else None,
                })
                
                print(f"✅ {other.user.username}: {score}%")
                print(f"   They teach: {other_teach}")
                print(f"   They learn: {other_learn}")
                print(f"   They can teach me: {they_can_teach_me}")
                print(f"   They want to learn from me: {i_can_teach_them}")
                print(f"   Score calculation: {match_count}/{total_skills} = {score}%")
                print()
        
        # Sort by score (highest first)
        match_list.sort(key=lambda x: x['score'], reverse=True)
        matches = match_list[:10]
    
    # Study feed
    study_feed = []
    for match in matches[:3]:
        study_feed.append({
            'user': match['name'],
            'action': match['skill_want'],
            'time_ago': 'Just now',
            'topic': match['skill_offer'],
            'goal': match['skill_want'],
            'likes': 0,
            'comments': 0
        })
    
    if not study_feed:
        study_feed = [
            {
                'user': 'StudyBuddy',
                'action': 'posted: Looking for study partner',
                'time_ago': '2 hours ago',
                'topic': 'Python',
                'goal': 'Django',
                'likes': 3,
                'comments': 1
            },
        ]
    
    # User activities
    user_activities = []
    requests = MatchRequest.objects.filter(receiver=request.user).order_by('-id')
    
    for req in requests:
        user_activities.append({
            'icon': 'person',
            'message': f"{req.sender.username} is interested in your skills",
            'date': timesince(req.created_at) if hasattr(req, 'created_at') else "recently",
            'id': req.id,
            'status': req.status,
            'sender': req.sender.username,
            'user_id': req.sender.id,
            'time': timesince(req.created_at) if hasattr(req, 'created_at') else "recently"
        })
    
    if matches and not requests:
        user_activities.append({
            'icon': 'person-plus', 
            'message': f'You have {len(matches)} new match suggestions', 
            'date': 'Today',
            'time': 'Today',
            'user_id': None,
            'id': None,
            'status': 'info'
        })
    
    if profile.updated_at:
        user_activities.append({
            'icon': 'pencil', 
            'message': 'Profile updated', 
            'date': 'Recently',
            'time': 'Recently',
            'user_id': None,
            'id': None,
            'status': 'info'
        })
    
    if not user_activities:
        user_activities.append({
            'icon': 'inbox',
            'message': 'No recent activity',
            'date': '',
            'time': '',
            'user_id': None,
            'id': None,
            'status': 'info'
        })
    
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
    
    recently_watched = []
    saved_items = []
    
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
        'recently_watched': recently_watched,
        'saved_items': saved_items,
    }
    
    print(f"\n{'='*60}")
    print(f"📊 FINAL MATCHES: {len(matches)}")
    for m in matches:
        print(f"   {m['name']}: {m['score']}%")
    print(f"{'='*60}\n")
    
    return render(request, 'dashboard/index.html', context)