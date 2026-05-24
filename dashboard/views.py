# dashboard/views.py
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from useraccount.models import UserProfile, UserSkill
from feedview.models import MatchRequest, Notification, Post
from django.utils.timesince import timesince
from datetime import datetime
from feedview.models import Like, Interested
import json

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
                # Base score + bonus for level compatibility
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

def calculate_match_score(my_teach, my_learn, other_teach, other_learn):
    """
    Legacy simple match score calculation (kept for compatibility)
    """
    my_teach_set = {skill.lower().strip() for skill in my_teach}
    my_learn_set = {skill.lower().strip() for skill in my_learn}
    other_teach_set = {skill.lower().strip() for skill in other_teach}
    other_learn_set = {skill.lower().strip() for skill in other_learn}
    
    they_can_teach_me = my_learn_set & other_teach_set
    i_can_teach_them = my_teach_set & other_learn_set
    
    total_skills = len(my_learn_set) + len(my_teach_set)
    
    if total_skills == 0:
        return 0
    
    match_score = len(they_can_teach_me) + len(i_can_teach_them)
    percentage = (match_score / total_skills) * 100
    
    return int(percentage)


@login_required
def dashboard_home(request):
    # Get current user's profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get current user's skills from UserSkill model
    my_teach_skills = profile.skills.filter(skill_type='teach')
    my_learn_skills = profile.skills.filter(skill_type='learn')
    
    # Legacy lists for compatibility
    my_teach = [s.skill_name for s in my_teach_skills]
    my_learn = [s.skill_name for s in my_learn_skills]
    
    # Debug output
    print(f"\n{'='*60}")
    print(f"🔍 DASHBOARD MATCHING FOR: {request.user.username}")
    print(f"{'='*60}")
    print(f"📚 You teach: {[(s.skill_name, s.proficiency_level) for s in my_teach_skills]}")
    print(f"🎯 You want to learn: {[(s.skill_name, s.proficiency_level) for s in my_learn_skills]}")
    print(f"{'='*60}\n")
    
    # If user has no skills, show empty matches
    if not my_teach_skills and not my_learn_skills:
        matches = []
    else:
        # Get all other users
        other_profiles = UserProfile.objects.exclude(user=request.user)
        
        # Calculate matches with enhanced scores
        match_list = []
        
        for other in other_profiles:
            # Get other user's skills from UserSkill model
            other_teach_skills = other.skills.filter(skill_type='teach')
            other_learn_skills = other.skills.filter(skill_type='learn')
            
            # Legacy lists for compatibility
            other_teach = [s.skill_name for s in other_teach_skills]
            other_learn = [s.skill_name for s in other_learn_skills]
            
            # Calculate enhanced score using proficiency levels
            enhanced_score, direct_matches = calculate_enhanced_match_score(profile, other)
            
            # Also calculate legacy score for comparison
            legacy_score = calculate_match_score(my_teach, my_learn, other_teach, other_learn)
            
            # Use enhanced score as primary
            score = enhanced_score
            
            if score > 0:
                # Find direct skill matches
                my_teach_names = {s.skill_name.lower() for s in my_teach_skills}
                my_learn_names = {s.skill_name.lower() for s in my_learn_skills}
                other_teach_names = {s.skill_name.lower() for s in other_teach_skills}
                other_learn_names = {s.skill_name.lower() for s in other_learn_skills}
                
                # They can teach me
                they_can_teach_me = list(my_learn_names & other_teach_names)
                # I can teach them
                i_can_teach_them = list(my_teach_names & other_learn_names)
                
                # Determine display skill and message
                if they_can_teach_me:
                    display_skill = they_can_teach_me[0].capitalize()
                    # Find the level
                    skill_obj = other_teach_skills.filter(skill_name__iexact=they_can_teach_me[0]).first()
                    level_info = f" ({skill_obj.proficiency_level})" if skill_obj else ""
                    display_message = f"can teach you {display_skill}{level_info}"
                elif i_can_teach_them:
                    display_skill = i_can_teach_them[0].capitalize()
                    skill_obj = my_teach_skills.filter(skill_name__iexact=i_can_teach_them[0]).first()
                    level_info = f" ({skill_obj.proficiency_level})" if skill_obj else ""
                    display_message = f"wants to learn {display_skill}{level_info}"
                else:
                    display_skill = other_teach[0].capitalize() if other_teach else "Skills"
                    display_message = "has skills to share"
                
                # Determine match strength
                if score >= 70:
                    match_strength = 'strong'
                elif score >= 40:
                    match_strength = 'medium'
                else:
                    match_strength = 'weak'
                
                # Prepare skills with levels for template
                skills_they_teach = [{'name': s.skill_name, 'level': s.proficiency_level, 'category': s.category} for s in other_teach_skills]
                skills_they_want = [{'name': s.skill_name, 'level': s.proficiency_level, 'category': s.category} for s in other_learn_skills]
                
                match_list.append({
                    'name': other.user.get_full_name() or other.user.username,
                    'skill_offer': display_skill,
                    'skill_want': display_message,
                    'score': score,
                    'legacy_score': legacy_score,
                    'profile_id': other.id,
                    'user_id': other.user.id,
                    'match_strength': match_strength,
                    'common_teach': i_can_teach_them,
                    'common_learn': they_can_teach_me,
                    'direct_matches': direct_matches,
                    'profile_picture': other.profile_picture.url if other.profile_picture else None,
                    'skills_they_teach': skills_they_teach,
                    'skills_they_want': skills_they_want,
                })
                
                print(f"✅ {other.user.username}: {score}% (Legacy: {legacy_score}%)")
                print(f"   They teach: {[(s.skill_name, s.proficiency_level) for s in other_teach_skills]}")
                print(f"   They learn: {[(s.skill_name, s.proficiency_level) for s in other_learn_skills]}")
                print(f"   Direct matches: {len(direct_matches)}")
                print(f"   Level compatible matches: {sum(1 for m in direct_matches if m['level_compatible'])}")
                print()
        
        # Sort by score (highest first)
        match_list.sort(key=lambda x: x['score'], reverse=True)
        matches = match_list[:10]
    
    # Study feed (using enhanced match data)
    study_feed = []
    for match in matches[:3]:
        study_feed.append({
            'user': match['name'],
            'action': match['skill_want'],
            'time_ago': 'Just now',
            'topic': match['skill_offer'],
            'goal': match['skill_want'],
            'likes': 0,
            'comments': 0,
            'match_strength': match.get('match_strength', 'weak')
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
                'comments': 1,
                'match_strength': 'info'
            },
        ]
    
    # User activities

    user_activities = list(
        Notification.objects.filter(
        receiver=request.user
        ).order_by('-created_at')
    )

# Add system notification for matches
    if matches:
        strong_matches = sum(
            1 for m in matches if m.get('match_strength') == 'strong'
        )

        user_activities.append({
            'sender': 'System',
            'message': f'You have {len(matches)} new match suggestions ({strong_matches} strong matches)',
            'time': 'Today',
            'user_id': None,
            'post_id': None,
            'notification_type': 'system'
        })

# Empty state
    if not user_activities:
        user_activities.append({
            'sender': 'System',
            'message': 'No recent activity',
            'time': '',
            'user_id': None,
            'post_id': None,
            'notification_type': 'system'
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
    unread_count = Notification.objects.filter(receiver=request.user, is_read=False).count()
    context = {
        'profile': profile,
        'matches': matches,
        'study_feed': study_feed,
        'user_activities': user_activities,
        'unread_count': unread_count,
        'weekly_hours': weekly_hours,
        'sessions_done': sessions_done,
        'streak_days': getattr(request.user, 'streak_days', 5),
        'consistency_percent': 75,
        'sql_progress': 65,
        'figma_progress': 40,
        'python_progress': 80,
        'time_of_day': get_time_of_day(),
        'matches_json': json.dumps(matches, default=str),  # Added default=str for datetime
        'today': datetime.now(),
        'recently_watched': recently_watched,
        'saved_items': saved_items,
        'my_teach_skills': [{'name': s.skill_name, 'level': s.proficiency_level, 'category': s.category} for s in my_teach_skills],
        'my_learn_skills': [{'name': s.skill_name, 'level': s.proficiency_level, 'category': s.category} for s in my_learn_skills],
    }
    
    print(f"\n{'='*60}")
    print(f"📊 FINAL MATCHES: {len(matches)}")
    for m in matches:
        print(f"   {m['name']}: {m['score']}% (Strength: {m.get('match_strength', 'N/A')})")
    print(f"{'='*60}\n")
    
    return render(request, 'dashboard/index.html', context)

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    post.is_liked = Like.objects.filter(
        user=request.user,
        post=post
    ).exists()

    post.user_interested = Interested.objects.filter(
        user=request.user,
        post=post
    ).exists()

    return render(request, 'feedview/post_detail.html', {
        'post': post
    })
from django.http import JsonResponse

@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(receiver=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)