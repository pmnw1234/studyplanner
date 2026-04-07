from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from useraccount.models import UserProfile # Assuming this is your profile model

@login_required
def dashboard_home(request):
    # 1. Get the current user's profile
 
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # 2. SMART MATCHING LOGIC
    
    my_teaching_skills = profile.skills_to_teach
    
    match_objs = UserProfile.objects.filter(
        skills_to_learn__in=my_teaching_skills
    ).exclude(user=request.user).distinct()[:4] # Top 4 matches

    # Formatting matches for your HTML template
    matches = []
    for m in match_objs:
        matches.append({
            'name': m.user.username,
            'skill_offer': m.skills_to_teach.first().name if m.skills_to_teach.exists() else "Various",
            'skill_want': m.skills_to_learn.first().name if m.skills_to_learn.exists() else "Learning",
            'score': 85, # You can calculate a real % score later!
        })

    # 3. MOCK DATA (Replace with real models later)
    study_feed = [
        {
            'user': 'Senior_Dev',
            'action': 'completed a 2-hour SQL sprint',
            'time_ago': '10 mins ago',
            'topic': 'Database Design',
            'goal': 'Advanced SQL',
            'likes': 12
        },
    ]

    user_activities = [
        {'icon': 'check-circle', 'message': 'You updated your Python progress', 'date': 'Today'},
        {'icon': 'people', 'message': 'New match found: Alex liked your SQL skill', 'date': 'Yesterday'},
    ]

    context = {
        'profile': profile,
        'matches': matches,
        'study_feed': study_feed,
        'user_activities': user_activities,
        'streak_days': 5, # Example
        'best_streak': 12,
        'consistency_percent': 75,
        'sql_progress': 65,
        'figma_progress': 40,
        'python_progress': 80,
    }

    return render(request, 'dashboard/index.html', context)