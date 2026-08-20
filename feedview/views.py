from django.contrib.auth import login, logout, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.utils.safestring import mark_safe
from django.contrib import messages

from useraccount.forms import (
    UserRegistrationForm,
    UserProfileEditForm,
    LoginForm,
    EnhancedUserProfileEditForm,
    CertificationForm
)
from useraccount.models import UserProfile, UserSkill, Certification
from feedview.models import MatchRequest, Post, Interested, Like, Comment, Notification
from Subscription.models import Subscription, Payment

@login_required
def feed_view(request):
    posts = Post.objects.all().order_by('-created_at')
    
    # Apply filters
    # category = request.GET.get('category')
    topic = request.GET.get('topic')
    hashtag = request.GET.get('hashtag')
    
    # if category:
    #     posts = posts.filter(category=category)
    if topic:
        posts = posts.filter(topic=topic)
    if hashtag:
        posts = posts.filter(hashtags__icontains=hashtag)
    
    for post in posts:
        post.user_interested = Interested.objects.filter(
            user=request.user,
            post=post
        ).exists()

        post.is_liked = Like.objects.filter(
            user=request.user,
            post=post
        ).exists()

    return render(request, 'feedview/feed.html', {
        'posts': posts,
        'users': User.objects.exclude(id=request.user.id)
    })

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
def inbox_view(request):
    requests = MatchRequest.objects.filter(
        receiver=request.user,
        status='pending'
    ).order_by('-created_at')

    my_profile = request.user.userprofile
    ai_matches = []

    all_profiles = UserProfile.objects.exclude(user=request.user)

    for profile in all_profiles:
        score, direct_matches = calculate_enhanced_match_score(
            my_profile,
            profile
        )

        if score > 0:
            ai_matches.append({
                "user": profile.user,
                "profile": profile,
                "score": score,
                "direct_matches": direct_matches,
                "teach_skills": profile.skills.filter(skill_type="teach"),
                "learn_skills": profile.skills.filter(skill_type="learn"),
            })

    ai_matches = sorted(
        ai_matches,
        key=lambda x: x["score"],
        reverse=True
    )

    return render(request, "feedview/inbox.html", {
        "requests": requests,
        "ai_matches": ai_matches,
    })
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

@login_required
def create_post(request):
    # Check if user has premium subscription
    subscription = Subscription.objects.filter(user=request.user).first()
    is_premium = subscription and subscription.is_premium() if subscription else False
    
    # Free users: Check post limit (4 posts per 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    weekly_posts = Post.objects.filter(
        user=request.user,
        created_at__gte=week_ago
    ).count()
    
    FREE_POST_LIMIT = 4

    if request.method == "POST":
        # Check if user has reached the limit (only for free users)
        if not is_premium and weekly_posts >= FREE_POST_LIMIT:
            messages.error(
                request,
                mark_safe(
                    'You have reached the free limit of 4 posts this week. '
                    '<a href="{}" style="color: var(--accent-primary); text-decoration: underline;">Upgrade to Premium</a> '
                    'to post unlimited content.'.format(reverse('plans'))
                )
            )
            return redirect("create_post")

        # Create the post
        post = Post.objects.create(
            user=request.user,
            content=request.POST.get("content"),
            post_type=request.POST.get("post_type", "study"),
            topic=request.POST.get("topic"),
            hashtags=request.POST.get("hashtags"),
            image=request.FILES.get("image"),
            video=request.FILES.get("video"),
        )

        messages.success(request, "Post created successfully!")
        return redirect("feed")

    # Calculate remaining posts for free users
    remaining_posts = 0
    if not is_premium:
        remaining_posts = max(0, FREE_POST_LIMIT - weekly_posts)
    
    # Check if user has a pending payment
    pending_payment = Payment.objects.filter(
        user=request.user,
        status='pending'
    ).first() if not is_premium else None

    context = {
        "remaining_posts": remaining_posts,
        "weekly_posts": weekly_posts,
        "is_premium": is_premium,
        "post_limit": FREE_POST_LIMIT if not is_premium else "Unlimited",
        "pending_payment": pending_payment,
    }

    return render(request, "feedview/create_post.html", context)

@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    like = post.likes.filter(user=request.user).first()

    if like:
        like.delete()
        status = 'unliked'
    else:
        post.likes.create(user=request.user)
        status = 'liked'

        if post.user != request.user:
            Notification.objects.create(
                sender=request.user,
                receiver=post.user,
                post=post,   # IMPORTANT
                notification_type='like',
                message=f"{request.user.username} liked your post"
            )

    return JsonResponse({
        'status': status,
        'total_likes': post.total_likes()
    })

@login_required
def interested_post(request, post_id):

    post = get_object_or_404(Post, id=post_id)

    interest = post.interests.filter(
        user=request.user
    ).first()

    note = request.POST.get('note', '').strip()

    if interest:

        interest.delete()

        Notification.objects.filter(
            sender=request.user,
            receiver=post.user,
            post=post,
            notification_type='interest'
        ).delete()

        status = 'uninterested'

    else:

        Interested.objects.create(
            user=request.user,
            post=post
        )

        status = 'interested'

        if post.user != request.user:

            Notification.objects.create(
                sender=request.user,
                receiver=post.user,
                post=post,
                notification_type='interest',
                message=f"{request.user.username} is interested in your post",
                note=note
            )

    return JsonResponse({
        'status': status,
        'total_interests': post.total_interested()
    })

def add_comment(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(Post, id=post_id)
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id') # Get parent_id from hidden input if it exists
        
        if content:
            comment = Comment(
                post=post,
                user=request.user,
                content=content
            )
            
            # If parent_id is present, link this comment as a reply
            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                comment.parent = parent_comment
                
            comment.save()
            
            # Optional: Trigger activity notification logic here if needed
            
        return redirect('feed') # Replace with your feed or post detail redirect namespace

@login_required
def send_request(request, user_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)
    
    receiver = get_object_or_404(User, id=user_id)
    
    if receiver == request.user:
        return JsonResponse({'status': 'error', 'message': 'Cannot send to yourself'}, status=400)
    
    existing = MatchRequest.objects.filter(
        sender=request.user,
        receiver=receiver
    ).first()
    
    if existing:
        return JsonResponse({'status': 'error', 'message': 'Request already sent'}, status=400)
    
    reverse_request = MatchRequest.objects.filter(
        sender=receiver,
        receiver=request.user
    ).first()
    
    if reverse_request:
        return JsonResponse({'status': 'error', 'message': 'They already sent you a request. Check your inbox!'}, status=400)
    
    MatchRequest.objects.create(
        sender=request.user,
        receiver=receiver,
        status='pending'
    )
    
    return JsonResponse({'status': 'sent', 'message': 'Request sent successfully'})
@login_required
def accept_request(request, request_id):
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

    return JsonResponse({
        'success': True
    })

@login_required
def comment_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')  # 1. Grab the parent comment identifier if it exists

        if content:
            # 2. Build the comment payload dynamically
            comment_kwargs = {
                'user': request.user,
                'post': post,
                'content': content
            }
            
            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                comment_kwargs['parent'] = parent_comment

            comment = Comment.objects.create(**comment_kwargs)

            # 3. Handle target notifications gracefully
            if post.user != request.user:
                Notification.objects.create(
                    sender=request.user,
                    receiver=post.user,
                    post=post,
                    notification_type='comment',
                    message=f"{request.user.username} commented on your post"
                )
            
            pfp_url = ""
            if hasattr(request.user, 'userprofile') and request.user.userprofile.profile_picture:
                pfp_url = request.user.userprofile.profile_picture.url

            # 4. Return the ID and Parent ID back to the front-end script
            return JsonResponse({
                'status': 'success',
                'comment_id': comment.id,
                'parent_id': comment.parent.id if comment.parent else None,
                'username': request.user.username,
                'user_id': request.user.id,
                'text': comment.content,
                'profile_picture': pfp_url,
                'total_comments': post.comments.count()
            })

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
def post_activity(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    def get_pfp(user):
        if hasattr(user, 'userprofile') and user.userprofile.profile_picture:
            return user.userprofile.profile_picture.url
        return ""

    likes = [{
        'id': like.user.id, 
        'username': like.user.username,
        'profile_picture': get_pfp(like.user)
    } for like in post.likes.all()]

    interests = [{
        'id': interest.user.id, 
        'username': interest.user.username,
        'profile_picture': get_pfp(interest.user)
    } for interest in post.interests.all()]

    # 5. Extract the parent layout so the frontend knows what is a reply
    comments = []
    for comment in post.comments.all():
        comments.append({
            'comment_id': comment.id,
            'parent_id': comment.parent.id if comment.parent else None,
            'user_id': comment.user.id,
            'user': comment.user.username,
            'text': comment.content,
            'profile_picture': get_pfp(comment.user)
        })

    return JsonResponse({
        'likes': likes,
        'interests': interests,
        'comments': comments
    })

@login_required
def decline_request(request, request_id):
    req = get_object_or_404(
        MatchRequest,
        id=request_id,
        receiver=request.user
    )

    req.delete()

    return JsonResponse({
        'success': True
    })


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)

    if request.method == 'POST':
        post.content = request.POST.get('content')
        post.post_type = 'study'
        post.topic = request.POST.get('topic')
        post.hashtags = request.POST.get('hashtags')

        # update image if new one uploaded
        if request.FILES.get('image'):
            post.image = request.FILES.get('image')

        # update video if new one uploaded
        if request.FILES.get('video'):
            post.video = request.FILES.get('video')

        post.is_edited = True   # optional if you show "edited"
        post.save()

        messages.success(request, "Post edited successfully.")
        return redirect('feed')

    return render(request, 'feedview/edit_post.html', {
        'post': post
    })


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, user=request.user)
    post.delete()
    messages.success(request, "Post deleted successfully.")
    return redirect('feed')

@login_required
def send_reply_view(request, activity_id):
    if request.method == 'POST':
        # 1. Fetch the original 'Interest' notification item that you're replying to
        original_notification = get_object_or_404(Notification, id=activity_id)
        
        # 2. Get the text written in the textarea
        reply_note_text = request.POST.get('reply_note', '').strip()
        
        if reply_note_text:
            # 3. Build the new notification object using your fields
            Notification.objects.create(
                sender=request.user,                     # The person logged in (you)
                receiver=original_notification.sender,   # The person who originally expressed interest
                post=original_notification.post,         # Connects it to the same post context
                notification_type='reply',               # Uses the new choice type
                message=f"{request.user.username} replied to your interest note.",
                note=reply_note_text,                    # Store their message body here
                is_read=False
            )
            messages.success(request, "Your reply has been sent!")
        else:
            messages.error(request, "Reply text cannot be empty.")
            
    # Redirect back to the page the user was on
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

def custom_404(request, exception=None):
    return render(request, '404.html', status=404)
