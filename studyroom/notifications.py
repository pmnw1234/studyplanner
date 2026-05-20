from django.utils import timezone
from datetime import timedelta
from .models import Notification, StudyRoom, ClassWork, Submission
from django.contrib.auth.models import User

def create_notification(recipient, sender, room, notification_type, title, message, work=None, submission=None):
    """Create a notification"""
    Notification.objects.create(
        recipient=recipient,
        sender=sender,
        room=room,
        work=work,
        submission=submission,
        notification_type=notification_type,
        title=title,
        message=message
    )

def notify_new_classwork(work):
    """Notify all students when new class work is created"""
    room = work.room
    
    for member in room.members.all():
        if member != room.creator:  # Don't notify creator
            create_notification(
                recipient=member,
                sender=room.creator,
                room=room,
                work=work,
                notification_type='new_work',
                title=f'New Assignment: {work.title}',
                message=f'{room.creator.username} posted a new assignment: {work.title}.'
            )

def notify_new_submission(submission):
    """Notify teacher when student submits work"""
    work = submission.work
    room = work.room
    create_notification(
        recipient=room.creator,
        sender=submission.student,
        room=room,
        work=work,
        submission=submission,
        notification_type='submission',
        title=f'New Submission: {work.title}',
        message=f'{submission.student.username} submitted "{work.title}"'
    )

def notify_grade(submission):
    """Notify student when work is graded"""
    create_notification(
        recipient=submission.student,
        sender=submission.work.room.creator,
        room=submission.work.room,
        work=submission.work,
        submission=submission,
        notification_type='graded',
        title=f'Your work was graded: {submission.work.title}',
        message=f'You received {submission.grade}% on "{submission.work.title}".'
    )

def check_upcoming_deadlines():
    """Check for deadlines within next 24 hours and notify students"""
    tomorrow = timezone.now() + timedelta(days=1)
    upcoming_works = ClassWork.objects.filter(
        due_date__gte=timezone.now(),
        due_date__lte=tomorrow
    )
    
    for work in upcoming_works:
        for submission in work.submissions.filter(status='pending'):
            existing = Notification.objects.filter(
                recipient=submission.student,
                work=work,
                notification_type='deadline',
                created_at__gte=timezone.now() - timedelta(hours=23)
            ).exists()
            
            if not existing:
                create_notification(
                    recipient=submission.student,
                    sender=work.room.creator,
                    room=work.room,
                    work=work,
                    notification_type='deadline',
                    title=f'⚠️ Deadline Approaching: {work.title}',
                    message=f'Your assignment "{work.title}" is due soon!'
                )