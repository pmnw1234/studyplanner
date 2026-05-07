from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json

from .models import Message
from useraccount.models import Connection

@login_required
@require_http_methods(["POST"])
def send_message(request, user_id):

    receiver = get_object_or_404(User, id=user_id)
    sender = request.user

    message_text = request.POST.get("message", "").strip()

    image = request.FILES.get("image")
    video = request.FILES.get("video")
    file = request.FILES.get("file")

    if not message_text and not image and not video and not file:
        return JsonResponse({
            'error': 'Message cannot be empty'
        }, status=400)

    message = Message.objects.create(
        sender=sender,
        receiver=receiver,
        message=message_text,
        image=image,
        video=video,
        file=file
    )

    return JsonResponse({
        'success': True,
        'message': message.message,
        'image': message.image.url if message.image else None,
        'video': message.video.url if message.video else None,
        'file': message.file.url if message.file else None,
        'time': message.created_at.strftime("%I:%M %p"),
    })
# @login_required
# @require_http_methods(["POST"])
# def send_message(request, user_id):
#     receiver = get_object_or_404(User, id=user_id)
#     sender = request.user
    
#     is_connected = Connection.objects.filter(
#         Q(user1=sender, user2=receiver) |
#         Q(user1=receiver, user2=sender)
#     ).exists()
    
#     if not is_connected:
#         return JsonResponse({'error': 'You can only message connected users'}, status=403)
    
#     try:
#         data = json.loads(request.body)
#         message_text = data.get('message', '').strip()
#     except json.JSONDecodeError:
#         return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
#     if not message_text:
#         return JsonResponse({'error': 'Message cannot be empty'}, status=400)
    
#     message = Message.objects.create(
#         sender=sender,
#         receiver=receiver,
#         message=message_text
#     )
    
#     return JsonResponse({
#         'success': True,
#         'message_id': message.id,
#         'message': message.message,
#         'time': message.created_at.strftime("%I:%M %p"),
#         'sender': sender.username
#     })


@login_required
def get_messages(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    current_user = request.user
    
    is_connected = Connection.objects.filter(
        Q(user1=current_user, user2=other_user) |
        Q(user1=other_user, user2=current_user)
    ).exists()
    
    if not is_connected:
        has_messages = Message.objects.filter(
            Q(sender=current_user, receiver=other_user) |
            Q(sender=other_user, receiver=current_user)
        ).exists()
        
        if not has_messages:
            return JsonResponse({'error': 'No conversation found'}, status=403)
    
    messages = Message.get_conversation(current_user, other_user)
    messages.filter(sender=other_user, receiver=current_user, is_read=False).update(is_read=True)
    
    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'message': msg.message,
            'time': msg.created_at.strftime("%I:%M %p"),
            'date': msg.created_at.strftime("%Y-%m-%d"),
            'is_mine': msg.sender == current_user,
            'is_read': msg.is_read,
            'image': msg.image.url if msg.image else None,
            'video': msg.video.url if msg.video else None,
            'file': msg.file.url if msg.file else None,
        })
    
    return JsonResponse({
        'messages': messages_data,
        'other_user': {
            'id': other_user.id,
            'username': other_user.username,
        }
    })


@login_required
def get_conversations(request):
    current_user = request.user
    
    sent_users = Message.objects.filter(sender=current_user).values_list('receiver', flat=True).distinct()
    received_users = Message.objects.filter(receiver=current_user).values_list('sender', flat=True).distinct()
    
    all_user_ids = set(list(sent_users) + list(received_users))
    
    conversations = []
    for user_id in all_user_ids:
        other_user = User.objects.get(id=user_id)
        
        last_message = Message.objects.filter(
            Q(sender=current_user, receiver=other_user) |
            Q(sender=other_user, receiver=current_user)
        ).last()
        
        unread_count = Message.objects.filter(
            sender=other_user, receiver=current_user, is_read=False
        ).count()
        
        profile_picture = None
        if hasattr(other_user, 'userprofile') and other_user.userprofile.profile_picture:
            profile_picture = other_user.userprofile.profile_picture.url
        
        conversations.append({
            'user_id': other_user.id,
            'username': other_user.username,
            'first_name': other_user.first_name,
            'last_name': other_user.last_name,
            'profile_picture': profile_picture,
            'last_message': last_message.message if last_message else '',
            'last_message_time': last_message.created_at.strftime("%I:%M %p") if last_message else '',
            'unread_count': unread_count,
        })
    
    conversations.sort(key=lambda x: x['last_message_time'], reverse=True)
    
    return JsonResponse({'conversations': conversations})


@login_required
def get_unread_count(request):
    count = Message.get_unread_count(request.user)
    return JsonResponse({'unread_count': count})


@login_required
@require_http_methods(["POST"])
def mark_as_read(request, message_id):
    message = get_object_or_404(Message, id=message_id, receiver=request.user)
    message.mark_as_read()
    return JsonResponse({'success': True})


@login_required
def mark_all_as_read(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    updated_count = Message.objects.filter(
        sender=other_user, receiver=request.user, is_read=False
    ).update(is_read=True)
    return JsonResponse({'success': True, 'marked_count': updated_count})

from django.shortcuts import render

@login_required
def conversation_list_view(request):
    """Render the conversation list page"""
    return render(request, 'direct_message/conversation_list.html')


@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    return render(request, 'direct_message/chat.html', {
        'other_user': other_user
    })