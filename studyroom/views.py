# studyplanner/studyroom/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import models
from .notifications import notify_new_classwork, notify_new_submission, notify_grade
from .models import StudyRoom, RoomActivity, ClassWork, WorkComment, Submission, RoomActivityLog, ScheduledCall, Note
from .forms import StudyRoomForm, ScheduledCallForm
import json

# ============================================
# EXISTING VIEWS (Keep these as they are)
# ============================================

@login_required
def studyroom_dashboard(request):
    my_rooms = request.user.study_rooms.all() | request.user.created_rooms.all()
    form = StudyRoomForm()
    return render(request, 'studyroom/dashboard.html', {
        'my_rooms': my_rooms.distinct(),
        'form': form
    })

# studyplanner/studyroom/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import models
from .notifications import notify_new_classwork, notify_new_submission, notify_grade
from .models import StudyRoom, RoomActivity, ClassWork, WorkComment, Submission, RoomActivityLog, ScheduledCall, Note
from .forms import StudyRoomForm, ScheduledCallForm
import json

# ... (your other views remain the same)

@login_required
def create_room(request):
    """Create a new study room"""
    if request.method == 'POST':
        form = StudyRoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.creator = request.user
            room.save()
            room.members.add(request.user)
            
            RoomActivity.objects.create(
                room=room,
                user=request.user,
                action='Created room'
            )
            
            messages.success(request, f"Study room '{room.course_name}' created successfully!")
            return redirect('studyroom:room_detail', room_id=room.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        messages.error(request, "Invalid request method.")
    
    return redirect('studyroom:studyroom_dashboard')

@login_required
def join_room(request):
    """Join an existing study room using room code"""
    if request.method == 'POST':
        code = request.POST.get('room_code', '').strip().upper()

        try:
            room = StudyRoom.objects.get(room_code=code)

            if request.user in room.members.all():
                messages.warning(request, "You already joined this room.")
                return redirect('studyroom:studyroom_dashboard')

            if room.is_full():
                messages.error(request, "Room is full (max 3 members).")
                return redirect('studyroom:studyroom_dashboard')

            room.members.add(request.user)

            RoomActivity.objects.create(
                room=room,
                user=request.user,
                action='Joined room'
            )

            messages.success(request, f"Joined room '{room.course_name}' successfully!")
            return redirect('studyroom:room_detail', room_id=room.id)

        except StudyRoom.DoesNotExist:
            messages.error(request, "Invalid room code.")
            return redirect('studyroom:studyroom_dashboard')
    
    return redirect('studyroom:studyroom_dashboard')
@login_required
def room_detail(request, room_id):
    room = get_object_or_404(StudyRoom, id=room_id)
    
    is_member = request.user in room.members.all() or request.user == room.creator
    
    members = list(room.members.all())
    if room.creator not in members:
        members.insert(0, room.creator)
    
    classworks = room.classworks.all().order_by('-created_at')
    
    if request.user == room.creator:
        classworks = classworks.prefetch_related(
            models.Prefetch('submissions', 
                queryset=Submission.objects.select_related('student__userprofile'),
                to_attr='prefetched_submissions'
            )
        )
    
    works_with_stream = []
    for work in classworks:
        stream_comments = work.comments.filter(user=work.created_by).order_by('-created_at')
        works_with_stream.append({
            'work': work,
            'stream_comments': stream_comments,
            'creator': work.created_by,
        })
    
    user_submissions = {}
    for work in classworks:
        try:
            submission = Submission.objects.get(work=work, student=request.user)
            user_submissions[work.id] = submission
        except Submission.DoesNotExist:
            user_submissions[work.id] = None
    
    assignments_count = classworks.filter(content_type='assignment').count()
    materials_count = classworks.filter(content_type='material').count()
    activity_logs = room.activity_logs.all()[:50]
    
    return render(request, 'studyroom/room_detail.html', {
        'room': room,
        'is_member': is_member,
        'members': members,
        'classworks': classworks,
        'works_with_stream': works_with_stream,
        'user_submissions': user_submissions,
        'activity_logs': activity_logs,
        'assignments_count': assignments_count,
        'materials_count': materials_count,
    })

@login_required
def create_classwork(request, room_id):
    room = get_object_or_404(StudyRoom, id=room_id)
    
    if request.user != room.creator:
        messages.error(request, "Only the room creator can add class work.")
        return redirect('room_detail', room_id=room.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        resource_title = request.POST.get('resource_title')
        resource_link = request.POST.get('resource_link')
        resource_file = request.FILES.get('resource_file')
        content_type = request.POST.get('content_type', 'assignment')
        
        if title:
            work = ClassWork.objects.create(
                room=room,
                title=title,
                description=description,
                created_by=request.user,
                due_date=due_date if due_date else None,
                resource_title=resource_title if resource_title else None,
                resource_link=resource_link if resource_link else None,
                resource_file=resource_file if resource_file else None,
                content_type=content_type
            )
            
            RoomActivityLog.objects.create(
                room=room,
                user=request.user,
                action='create_work',
                details=f'Created {content_type}: {title}'
            )
            
            if content_type == 'assignment':
                try:
                    notify_new_classwork(work)
                except ImportError:
                    pass
            
            messages.success(request, f"{content_type.title()} created successfully!")
        else:
            messages.error(request, "Title is required.")
    
    return redirect('room_detail', room_id=room.id)

@login_required
def edit_classwork(request, work_id):
    work = get_object_or_404(ClassWork, id=work_id)
    room = work.room
    
    if request.user != room.creator:
        messages.error(request, "Only the room creator can edit class work.")
        return redirect('room_detail', room_id=room.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        resource_title = request.POST.get('resource_title')
        resource_link = request.POST.get('resource_link')
        resource_file = request.FILES.get('resource_file')
        
        if title:
            work.title = title
            work.description = description
            work.due_date = due_date if due_date else None
            work.resource_title = resource_title if resource_title else None
            work.resource_link = resource_link if resource_link else None
            
            if resource_file:
                if work.resource_file:
                    work.resource_file.delete()
                work.resource_file = resource_file
            
            work.save()
            
            RoomActivityLog.objects.create(
                room=room,
                user=request.user,
                action='edit_work',
                details=f'Edited: {title}'
            )
            
            messages.success(request, "Class work updated successfully!")
    
    return redirect('room_detail', room_id=room.id)

@login_required
def delete_classwork(request, work_id):
    work = get_object_or_404(ClassWork, id=work_id)
    room = work.room
    
    if request.user != room.creator:
        messages.error(request, "Only the room creator can delete class work.")
        return redirect('room_detail', room_id=room.id)
    
    if request.method == 'POST':
        title = work.title
        work.delete()
        
        RoomActivityLog.objects.create(
            room=room,
            user=request.user,
            action='delete_work',
            details=f'Deleted: {title}'
        )
        
        messages.success(request, "Class work deleted successfully!")
    
    return redirect('room_detail', room_id=room.id)

@login_required
def submit_work(request, work_id):
    work = get_object_or_404(ClassWork, id=work_id)
    room = work.room
    
    if request.user not in room.members.all() and request.user != room.creator:
        messages.error(request, "You must be a room member to submit work.")
        return redirect('room_detail', room_id=room.id)
    
    submission, created = Submission.objects.get_or_create(
        work=work,
        student=request.user,
        defaults={'status': 'pending'}
    )
    
    if request.method == 'POST':
        content = request.POST.get('content', '')
        file = request.FILES.get('file')
        
        if content:
            submission.content = content
        if file:
            submission.file = file
        
        submission.status = 'submitted'
        submission.submitted_at = timezone.now()
        submission.save()
        
        RoomActivityLog.objects.create(
            room=room,
            user=request.user,
            action='submit_work',
            details=f'Submitted: {work.title}'
        )
        
        try:
            notify_new_submission(submission)
        except ImportError:
            pass
        
        messages.success(request, "Work submitted successfully!")
    
    return redirect('room_detail', room_id=room.id)

@login_required
def add_stream_comment(request, work_id):
    work = get_object_or_404(ClassWork, id=work_id)
    room = work.room
    
    if request.user != work.created_by:
        messages.error(request, "Only the creator of this work can post stream updates.")
        return redirect('room_detail', room_id=room.id)
    
    if request.method == 'POST':
        comment_text = request.POST.get('comment_text', '').strip()
        
        if comment_text:
            WorkComment.objects.create(
                work=work,
                user=request.user,
                text=comment_text
            )
            
            RoomActivity.objects.create(
                room=room,
                user=request.user,
                action=f'Posted stream update on: {work.title}'
            )
            
            messages.success(request, "Stream update posted!")
        else:
            messages.error(request, "Comment cannot be empty.")
    
    return redirect('room_detail', room_id=room.id)

@login_required
def grade_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    room = submission.work.room
    
    if request.user != room.creator:
        messages.error(request, "Only the room creator can grade submissions.")
        return redirect('room_detail', room_id=room.id)
    
    if request.method == 'POST':
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback', '')
        
        if grade:
            submission.grade = grade
            submission.feedback = feedback
            submission.status = 'graded'
            submission.save()
            
            RoomActivityLog.objects.create(
                room=room,
                user=request.user,
                action='grade_work',
                details=f'Graded: {submission.work.title} for {submission.student.username}'
            )
            
            try:
                notify_grade(submission)
            except ImportError:
                pass
            
            messages.success(request, f"Graded {submission.student.username}'s work!")
    
    return redirect('room_detail', room_id=room.id)

@login_required
def leave_room(request, room_id):
    room = get_object_or_404(StudyRoom, id=room_id)
    
    if request.user == room.creator:
        messages.error(request, "Creator cannot leave. Transfer ownership first or delete the room.")
        return redirect('room_detail', room_id=room.id)
    
    if request.user in room.members.all():
        room.members.remove(request.user)
        
        RoomActivityLog.objects.create(
            room=room,
            user=request.user,
            action='leave',
            details=f'{request.user.username} left the room'
        )
        
        messages.success(request, "You have left the room.")
    else:
        messages.error(request, "You are not a member of this room.")
    
    return redirect('studyroom_dashboard')

@login_required
def transfer_ownership(request, room_id):
    room = get_object_or_404(StudyRoom, id=room_id)
    
    if request.user != room.creator:
        messages.error(request, "Only the room creator can transfer ownership.")
        return redirect('room_detail', room_id=room.id)
    
    if request.method == 'POST':
        new_owner_id = request.POST.get('new_owner')
        new_owner = get_object_or_404(User, id=new_owner_id)
        
        if new_owner not in room.members.all():
            messages.error(request, "New owner must be a room member.")
        else:
            room.creator = new_owner
            room.save()
            room.members.add(request.user)
            
            RoomActivityLog.objects.create(
                room=room,
                user=request.user,
                action='leave',
                details=f'Ownership transferred to {new_owner.username}'
            )
            
            messages.success(request, f"Room ownership transferred to {new_owner.username}.")
    
    return redirect('room_detail', room_id=room.id)

@login_required
def notification_api(request):
    notifications = request.user.notifications.all()[:20]
    unread_count = request.user.notifications.filter(is_read=False).count()
    
    data = {
        'unread_count': unread_count,
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.notification_type,
                'is_read': n.is_read,
                'time_ago': n.created_at.strftime('%b %d, %H:%M'),
                'room_url': f"/library/room/{n.room.id}/" if n.room else None
            }
            for n in notifications
        ]
    }
    return JsonResponse(data)

@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'studyroom_dashboard'))

@login_required
def notes_list(request):
    notes = Note.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'studyroom/notes.html', {'notes': notes})

@login_required
def delete_note(request, note_id):
    if request.method == 'DELETE':
        note = get_object_or_404(Note, id=note_id, user=request.user)
        note.delete()
        return JsonResponse({'status': 'deleted'})
    return JsonResponse({'error': 'Invalid method'}, status=400)


# ============================================
# NEW: VIDEO CALL & CALENDAR VIEWS
# ============================================

@login_required
def calendar_data(request, room_id):
    """API endpoint for calendar events"""
    room = get_object_or_404(StudyRoom, id=room_id)
    
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    calls = ScheduledCall.objects.filter(
        room=room,
        status__in=['scheduled', 'ongoing']
    )
    
    if start:
        calls = calls.filter(start_time__gte=start)
    if end:
        calls = calls.filter(end_time__lte=end)
    
    events = []
    for call in calls:
        is_ongoing = call.is_ongoing()
        events.append({
            'id': str(call.id),
            'title': call.title,
            'start': call.start_time.isoformat(),
            'end': call.end_time.isoformat(),
            'description': call.description or '',
            'url': call.get_absolute_url(),
            'extendedProps': {
                'created_by': call.created_by.username,
                'status': call.status,
                'jitsi_room_id': call.jitsi_room_id,
                'meeting_url': call.get_meeting_url(),
                'is_ongoing': is_ongoing,
                'call_id': call.id,
            },
            'backgroundColor': '#4F46E5' if call.status == 'scheduled' else '#10B981',
            'borderColor': '#4F46E5' if call.status == 'scheduled' else '#10B981',
            'textColor': '#FFFFFF',
        })
    
    return JsonResponse(events, safe=False)

@login_required
def upcoming_calls(request, room_id):
    """Get upcoming calls for a room"""
    room = get_object_or_404(StudyRoom, id=room_id)
    now = timezone.now()
    
    upcoming = ScheduledCall.objects.filter(
        room=room,
        start_time__gte=now,
        status__in=['scheduled']
    ).order_by('start_time')[:5]
    
    data = [{
        'id': call.id,
        'title': call.title,
        'start_time': call.start_time.isoformat(),
        'end_time': call.end_time.isoformat(),
        'created_by': call.created_by.username,
        'jitsi_room_id': call.jitsi_room_id,
        'meeting_url': call.get_meeting_url(),
        'is_ongoing': call.is_ongoing(),
    } for call in upcoming]
    
    return JsonResponse({'upcoming_calls': data})

@login_required
@require_http_methods(["GET", "POST"])
def schedule_call(request, room_id):
    """Schedule a new video call"""
    room = get_object_or_404(StudyRoom, id=room_id)
    
    # Check permission
    if request.user not in room.members.all() and request.user != room.creator:
        messages.error(request, "You don't have permission to schedule calls.")
        return redirect('studyroom:room_detail', room_id=room.id)
    
    if request.method == 'POST':
        form = ScheduledCallForm(request.POST)
        if form.is_valid():
            call = form.save(commit=False)
            call.room = room
            call.created_by = request.user
            call.save()
            
            # Log activity
            try:
                RoomActivityLog.objects.create(
                    room=room,
                    user=request.user,
                    action='create_work',
                    details=f'Scheduled video call: {call.title}'
                )
            except:
                pass
            
            messages.success(request, f'Video call "{call.title}" scheduled successfully!')
            return redirect('studyroom:room_detail', room_id=room.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('studyroom:room_detail', room_id=room.id)
    
    # GET request - redirect to room detail
    return redirect('studyroom:room_detail', room_id=room.id)

@login_required
def join_call(request, jitsi_room_id):
    """Join a video call"""
    print(f"🔵 join_call called with jitsi_room_id: {jitsi_room_id}")
    
    try:
        call = get_object_or_404(ScheduledCall, jitsi_room_id=jitsi_room_id)
        print(f"✅ Found call: {call.title}")
    except Exception as e:
        print(f"❌ Error finding call: {e}")
        messages.error(request, "Call not found. Please check the link.")
        return redirect('studyroom:studyroom_dashboard')
    
    # Check access
    room = call.room
    if request.user not in room.members.all() and request.user != room.creator:
        messages.error(request, "You don't have access to this call.")
        return redirect('studyroom:studyroom_dashboard')
    
    # Update status
    call.save()
    
    print(f"📹 Call status: {call.status}, is_ongoing: {call.is_ongoing()}")
    print(f"🔗 Meeting URL: {call.get_meeting_url()}")
    
    context = {
        'call': call,
        'room': room,
        'meeting_url': call.get_meeting_url(),
        'is_ongoing': call.is_ongoing(),
        'time_until_start': (call.start_time - timezone.now()).total_seconds() if call.start_time > timezone.now() else 0,
    }
    return render(request, 'studyroom/join_call.html', context)

@login_required
@require_http_methods(["POST"])
def cancel_call(request, call_id):
    """Cancel a scheduled call"""
    call = get_object_or_404(ScheduledCall, id=call_id)
    
    if request.user != call.created_by:
        return JsonResponse({'error': 'You cannot cancel this call'}, status=403)
    
    call.status = 'cancelled'
    call.save()
    
    return JsonResponse({'success': True})