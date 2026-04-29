import profile

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import MatchRequest, Post, Like, Interested
from django.contrib.auth.models import User
from useraccount.models import UserProfile
from django.views.decorators.http import require_POST
from django.http import JsonResponse

@login_required
def feed_view(request):
    users = User.objects.exclude(id=request.user.id)
    db_posts = Post.objects.all().order_by('-created_at')

    return render(request, 'feedview/feed.html', {'posts': db_posts, 'users':users})



@login_required
def inbox_view(request):
    requests = MatchRequest.objects.filter(
        receiver=request.user
    ).order_by('-created_at')

    return render(request, 'feedview/inbox.html', {'requests': requests})

@require_POST
@login_required
def accept_request(request, request_id):
    req = get_object_or_404(MatchRequest, id=request_id, receiver=request.user)

    req.status = 'accepted'
    req.save()

    # Ensure profiles exist
    sender_profile, _ = UserProfile.objects.get_or_create(user=req.sender)
    receiver_profile, _ = UserProfile.objects.get_or_create(user=req.receiver)

    # Increase count
    sender_profile.study_partners_count += 1
    receiver_profile.study_partners_count += 1

    sender_profile.save()
    receiver_profile.save()

    return redirect('inbox')


@require_POST
@login_required
def decline_request(request, request_id):
    req = get_object_or_404(MatchRequest, id=request_id, receiver=request.user)

    req.status = 'declined'
    req.save()

    return redirect('inbox')


@login_required
def send_request(request, user_id):
    if request.user.id == user_id:
        return redirect('feed')

    # 🔥 Check BOTH directions
    existing = MatchRequest.objects.filter(
        sender=request.user,
        receiver_id=user_id
    ).first()

    reverse_existing = MatchRequest.objects.filter(
        sender_id=user_id,
        receiver=request.user
    ).first()

    # ✅ Case 1: Already sent
    if existing:
        if existing.status == 'pending':
            return redirect('feed')

        elif existing.status == 'accepted':
            return redirect('feed')

        elif existing.status == 'declined':
            existing.status = 'pending'
            existing.save()
            return redirect('feed')

    # ✅ Case 2: Reverse exists (very important)
    if reverse_existing:
        if reverse_existing.status == 'pending':
            # auto accept (like Facebook)
            reverse_existing.status = 'accepted'
            reverse_existing.save()

            # update partner count
            sender_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            receiver_profile, _ = UserProfile.objects.get_or_create(user=reverse_existing.sender)

            sender_profile.study_partners_count += 1
            receiver_profile.study_partners_count += 1

            sender_profile.save()
            receiver_profile.save()

        return redirect('feed')

    obj, created = MatchRequest.objects.get_or_create(
    sender=request.user,
    receiver_id=user_id,
    defaults={'status': 'pending'}
)

# If already exists, handle status
    if not created:
        if obj.status == 'declined':
            obj.status = 'pending'
            obj.save()

    return redirect('feed')
@login_required
def like_post(request, post_id):
    post = Post.objects.get(id=post_id)

    like, created = Like.objects.get_or_create(
        user=request.user,
        post=post
    )

    if not created:
        like.delete()

    return redirect('feed')

@login_required
def create_post(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        post_type = request.POST.get('post_type')
        image = request.FILES.get('image')
        video = request.FILES.get('video')

        Post.objects.create(
            user=request.user,
            content=content,
            post_type=post_type,
            image=image,
            video=video
        )

        return redirect('feed')

    return render(request, 'feedview/create_post.html')