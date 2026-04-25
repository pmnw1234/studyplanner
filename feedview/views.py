from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import MatchRequest
from django.contrib.auth.models import User

@login_required
def feed_view(request):

    users = User.objects.exclude(id=request.user.id)

    posts = []

    for i, u in enumerate(users[:3]):  # get real users
        posts.append({
            'id': i + 1,
            'user': u.username,
            'user_id': u.id,   # ✅ REAL ID
            'content': f'{u.username} is studying something cool!',
            'likes': i * 2
        })

    liked_posts = request.session.get('liked_posts', [])

    for post in posts:
        if post['id'] in liked_posts:
            post['likes'] += 1

    user_posts = request.session.get('user_posts', [])

    if request.method == 'POST':
        content = request.POST.get('content')

        if content:
            new_post = {
                'id': len(user_posts) + 100,
                'user': request.user.username,
                'content': content,
                'likes': 0
            }
            user_posts.insert(0, new_post)
            request.session['user_posts'] = user_posts
            return redirect('feed')
        

    all_posts = user_posts + posts

    return render(request, 'feedview/feed.html', {'posts': all_posts})


@login_required
def inbox_view(request):
    requests = MatchRequest.objects.filter(receiver=request.user, status='pending')
    return render(request, 'feedview/inbox.html', {'requests': requests})


@login_required
def accept_request(request, request_id):
    req = get_object_or_404(MatchRequest, id=request_id)
    req.status = 'accepted'
    req.save()
    return redirect('inbox')


@login_required
def decline_request(request, request_id):
    req = get_object_or_404(MatchRequest, id=request_id)
    req.status = 'declined'
    req.save()
    return redirect('inbox')


@login_required
def send_request(request, user_id):

    if user_id == request.user.id:
        return redirect('feed')  # ❌ don't send to yourself

    # ✅ prevent duplicate requests
    existing = MatchRequest.objects.filter(
        sender=request.user,
        receiver_id=user_id,
        status='pending'
    ).first()

    if not existing:
        MatchRequest.objects.create(
            sender=request.user,
            receiver_id=user_id
        )

    return redirect('feed')
@login_required
def like_post(request, post_id):

    liked_posts = request.session.get('liked_posts', [])

    if post_id not in liked_posts:
        liked_posts.append(post_id)

    request.session['liked_posts'] = liked_posts

    return redirect('feed')