from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from useraccount.models import Connection
import json

from .models import Message, GroupChat
from useraccount.models import Connection, UserProfile


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

@login_required
@require_http_methods(["POST"])
def send_group_message(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id, members=request.user)
    
    message_text = request.POST.get("message", "").strip()
    image = request.FILES.get("image") if "image" in request.FILES else None
    video = request.FILES.get("video") if "video" in request.FILES else None
    file = request.FILES.get("file") if "file" in request.FILES else None

    if not message_text and not image and not video and not file:
        return JsonResponse({'success': False, 'error': 'Message cannot be empty'}, status=400)

    try:
        # FIX: Satisfy SQLite's NOT NULL constraint by using request.user as a placeholder receiver
        message = Message.objects.create(
            sender=request.user,
            receiver=request.user,  # <--- This satisfies the NOT NULL constraint perfectly!
            group=group,    
            message=message_text,
            image=image,
            video=video,
            file=file
        )
        return JsonResponse({'success': True})
        
    except Exception as e:
        print("GROUP SEND ERROR:", str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def delete_group_chat(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id)
    
    # Check permission without using the non-existent field 'owner'
    if request.user.username == "myo123":
        group.delete()
        # Use an absolute URL path here to prevent double-prefix issues
        return redirect('/messages/')
        
    return HttpResponseForbidden("You are not authorized to delete this group.")
    

@login_required
def get_group_messages(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id, members=request.user)
    current_user = request.user
    
    # Pull messages tied to this group context
    messages = Message.objects.filter(group=group).order_by('created_at')
    
    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'sender_id': msg.sender.id,
            'message': msg.message,
            'time': msg.created_at.strftime("%I:%M %p"),
            'date': msg.created_at.strftime("%Y-%m-%d"),
            'is_mine': msg.sender == current_user,
            'image': msg.image.url if msg.image else None,
            'video': msg.video.url if msg.video else None,
            'file': msg.file.url if msg.file else None,
        })
    
    return JsonResponse({
        'messages': messages_data,
        'group': {
            'id': group.id,
            'name': group.name,
        }
    })

@login_required
def get_messages(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    current_user = request.user
    
    # Check if users are connected (or have exchanged messages)
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
            'full_name': other_user.get_full_name() or other_user.username,
        }
    })


from django.utils import timezone

@login_required
def get_conversations(request):
    current_user = request.user
    
    # Capture search text query parameter from AJAX request if present
    search_query = request.GET.get('search', '').strip().lower()

    # 1. FETCH DIRECT MESSAGES USER CONVERSATIONS (Filter out any group messages!)
    sent_users = Message.objects.filter(sender=current_user, group__isnull=True).values_list('receiver', flat=True).distinct()
    received_users = Message.objects.filter(receiver=current_user, group__isnull=True).values_list('sender', flat=True).distinct()
    
    # Combine IDs while removing yourself from direct conversations list
    all_user_ids = set(list(sent_users) + list(received_users))
    if current_user.id in all_user_ids:
        all_user_ids.remove(current_user.id)

    conversations = []

    # Build user items
    for user_id in all_user_ids:
        try:
            other_user = User.objects.get(id=user_id)
            
            # Apply Search Filtering on Usernames/Names
            full_name = (other_user.get_full_name() or other_user.username).lower()
            if search_query and (search_query not in other_user.username.lower() and search_query not in full_name):
                continue

            last_message = Message.objects.filter(
                group__isnull=True
            ).filter(
                Q(sender=current_user, receiver=other_user) |
                Q(sender=other_user, receiver=current_user)
            ).last()

            unread_count = Message.objects.filter(
                sender=other_user, receiver=current_user, is_read=False, group__isnull=True
            ).count()

            profile_picture = None
            try:
                if hasattr(other_user, 'userprofile') and other_user.userprofile and other_user.userprofile.profile_picture:
                    profile_picture = other_user.userprofile.profile_picture.url
            except Exception:
                profile_picture = None

            conversations.append({
                'is_group': False,
                'user_id': other_user.id,
                'username': other_user.username,
                'name': other_user.get_full_name() or other_user.username,
                'profile_picture': profile_picture,
                'last_message': last_message.message if last_message else '',
                'raw_time': last_message.created_at if last_message else None,
                'last_message_time': last_message.created_at.strftime("%I:%M %p") if last_message else '',
                'unread_count': unread_count,
            })
        except User.DoesNotExist:
            continue

    # 2. FETCH GROUP CHATS (Check if user belongs to group members)
    user_groups = GroupChat.objects.filter(members=current_user)
    for group in user_groups:
        # Apply Search Filtering on Group Names
        if search_query and search_query not in group.name.lower():
            continue

        last_group_msg = Message.objects.filter(group=group).last()

        conversations.append({
            'is_group': True,
            'group_id': group.id,
            'name': group.name,
            'profile_picture': None, # Group placeholder
            'last_message': f"Group: {last_group_msg.message}" if last_group_msg else 'No messages yet',
            'raw_time': last_group_msg.created_at if last_group_msg else group.created_at,
            'last_message_time': last_group_msg.created_at.strftime("%I:%M %p") if last_group_msg else '',
            'unread_count': 0, # Manage via custom tracking if preferred later
        })

    # Sort conversations accurately using datetime objects instead of string text
    conversations.sort(key=lambda x: x['raw_time'] if x['raw_time'] else current_user.date_joined, reverse=True)

    # Clean up datetime references before rendering JsonResponse output
    for c in conversations:
        c.pop('raw_time', None)

    return JsonResponse({'conversations': conversations})


@login_required
def get_unread_count(request):
    try:
        count = Message.get_unread_count(request.user)
        return JsonResponse({'unread_count': count})
    except Exception as e:
        print(f"Error getting unread count: {e}")
        return JsonResponse({'unread_count': 0})


@login_required
@require_http_methods(["POST"])
def mark_as_read(request, message_id):
    try:
        message = get_object_or_404(Message, id=message_id, receiver=request.user)
        message.mark_as_read()
        return JsonResponse({'success': True})
    except Exception as e:
        print(f"Error marking message as read: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def mark_all_as_read(request, user_id):
    try:
        other_user = get_object_or_404(User, id=user_id)
        updated_count = Message.objects.filter(
            sender=other_user, receiver=request.user, is_read=False
        ).update(is_read=True)
        return JsonResponse({'success': True, 'marked_count': updated_count})
    except Exception as e:
        print(f"Error marking all as read: {e}")
        return JsonResponse({'error': str(e)}, status=500)


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

@login_required
def get_friends(request):
    try:
        # Temporarily get all users so you can test group creation successfully!
        friends = User.objects.exclude(id=request.user.id)

        friends_list = []
        for friend in friends:
            profile_picture = None
            if hasattr(friend, 'userprofile') and friend.userprofile:
                profile_picture = friend.userprofile.profile_picture.url if friend.userprofile.profile_picture else None

            friends_list.append({
                'user_id': friend.id,
                'username': friend.username,
                'first_name': friend.first_name,
                'last_name': friend.last_name,
                'profile_picture': profile_picture,
            })

        return JsonResponse({'friends': friends_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def create_group_chat(request):
    try:
        data = json.loads(request.body)
        group_name = data.get('name')
        member_ids = data.get('members', [])

        if not group_name:
            return JsonResponse({'success': False, 'error': 'Group name is required'}, status=400)

        group = GroupChat.objects.create(name=group_name)
        group.members.add(request.user)
        for m_id in member_ids:
            group.members.add(m_id)

        # Send back a clean URL path so the JavaScript knows exactly where to redirect
        return JsonResponse({
            'success': True, 
            'group_id': group.id,
            'redirect_url': f'/messages/group-chat/{group.id}/'  # Match your group chat URL path structure
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@login_required
def group_chat_view(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id, members=request.user)
    
    # Since there is no owner field, fallback to checking if 'myo123' is the current user 
    # or handle ownership by checking the first member in the set
    is_owner = (request.user.username == "myo123")
    
    # We will pick a representative user to mark as 'owner' visually in the sidebar template
    group_owner = group.members.filter(username="myo123").first() or group.members.first()

    return render(request, 'direct_message/group_chat.html', {
        'group': group,
        'group_owner': group_owner,
        'is_owner': is_owner
    })

@login_required
@require_http_methods(["POST"])
def leave_group_chat(request, group_id):
    group = get_object_or_404(GroupChat, id=group_id, members=request.user)
    group.members.remove(request.user)
    
    # Clean up the group entirely if no users are left inside it
    if group.members.count() == 0:
        group.delete()
        
    return redirect('/messages/') # Change to your standard core messaging page URL configuration path

        