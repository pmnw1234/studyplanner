from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User

from .models import StudyRoom, RoomActivity, ClassWork, WorkComment, Submission, RoomActivityLog
from .forms import StudyRoomForm


@login_required
def studyroom_dashboard(request):
    my_rooms = request.user.study_rooms.all() | request.user.created_rooms.all()

    form = StudyRoomForm()

    return render(request, 'studyroom/dashboard.html', {
        'my_rooms': my_rooms.distinct(),
        'form': form
    })


@login_required
def create_room(request):
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

            messages.success(request, "Study room created successfully!")

    return redirect('studyroom_dashboard')


@login_required
def join_room(request):
    if request.method == 'POST':
        code = request.POST.get('room_code', '').strip().upper()

        try:
            room = StudyRoom.objects.get(room_code=code)

            if request.user in room.members.all():
                messages.warning(request, "You already joined this room.")
                return redirect('studyroom_dashboard')

            if room.is_full():
                messages.error(request, "Room is full (max 3 members).")
                return redirect('studyroom_dashboard')

            room.members.add(request.user)

            RoomActivity.objects.create(
                room=room,
                user=request.user,
                action='Joined room'
            )

            messages.success(request, "Joined room successfully!")

        except StudyRoom.DoesNotExist:
            messages.error(request, "Invalid room code.")

    return redirect('studyroom_dashboard')


@login_required
def room_detail(request, room_id):
    room = get_object_or_404(StudyRoom, id=room_id)
    
    # Check if user is a member or creator
    is_member = request.user in room.members.all() or request.user == room.creator
    
    # Get all members (including creator)
    members = list(room.members.all())
    if room.creator not in members:
        members.insert(0, room.creator)
    
    # Get class works for this room
    classworks = room.classworks.all().order_by('-created_at')
    
    # Prepare stream data: for each class work, get comments
    works_with_stream = []
    for work in classworks:
        stream_comments = work.comments.filter(user=work.created_by).order_by('-created_at')
        works_with_stream.append({
            'work': work,
            'stream_comments': stream_comments,
            'creator': work.created_by,
        })
    
    # Get submissions for current user (for class work tab)
    user_submissions = {}
    for work in classworks:
        try:
            submission = Submission.objects.get(work=work, student=request.user)
            user_submissions[work.id] = submission
        except Submission.DoesNotExist:
            user_submissions[work.id] = None
    
    # Get all submissions for creator view
    all_submissions = {}
    if request.user == room.creator:
        for work in classworks:
            all_submissions[work.id] = work.submissions.all().select_related('student')
    
    # Get activity logs
    activity_logs = room.activity_logs.all()[:50]
    
    return render(request, 'studyroom/room_detail.html', {
        'room': room,
        'is_member': is_member,
        'members': members,
        'classworks': classworks,
        'works_with_stream': works_with_stream,
        'user_submissions': user_submissions,
        'all_submissions': all_submissions,
        'activity_logs': activity_logs,
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
        
        if title:
            work = ClassWork.objects.create(
                room=room,
                title=title,
                description=description,
                created_by=request.user,
                due_date=due_date if due_date else None,
                resource_title=resource_title if resource_title else None,
                resource_link=resource_link if resource_link else None,
                resource_file=resource_file if resource_file else None
            )
            
            RoomActivityLog.objects.create(
                room=room,
                user=request.user,
                action='create_work',
                details=f'Created class work: {title}'
            )
            
            messages.success(request, "Class work created successfully!")
        else:
            messages.error(request, "Title is required.")
    
    return redirect('room_detail', room_id=room.id)

@login_required
def add_stream_comment(request, work_id):
    work = get_object_or_404(ClassWork, id=work_id)
    room = work.room
    
    # Only the person who created the work can comment on their own work's stream
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


# Class Work: Edit
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
                # Delete old file if exists
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

# Class Work: Delete
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


# Submit work (for students)
@login_required
def submit_work(request, work_id):
    work = get_object_or_404(ClassWork, id=work_id)
    room = work.room
    
    # Check if user is a member
    if request.user not in room.members.all() and request.user != room.creator:
        messages.error(request, "You must be a room member to submit work.")
        return redirect('room_detail', room_id=room.id)
    
    # Check if already submitted
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
        
        messages.success(request, "Work submitted successfully!")
    
    return redirect('room_detail', room_id=room.id)


# Grade submission (only creator)
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
            
            messages.success(request, f"Graded {submission.student.username}'s work!")
    
    return redirect('room_detail', room_id=room.id)


# Leave room
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


# Transfer ownership (creator can transfer to another member)
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
            # Transfer ownership
            room.creator = new_owner
            room.save()
            
            # Add old creator as regular member
            room.members.add(request.user)
            
            RoomActivityLog.objects.create(
                room=room,
                user=request.user,
                action='leave',
                details=f'Ownership transferred to {new_owner.username}'
            )
            
            messages.success(request, f"Room ownership transferred to {new_owner.username}.")
    
    return redirect('room_detail', room_id=room.id)