# studyplanner/studyroom/urls.py

from django.urls import path
from . import views

app_name = 'studyroom'

urlpatterns = [
    # Dashboard
    path('library/', views.studyroom_dashboard, name='studyroom_dashboard'),
    
    # Room management
    path('create-room/', views.create_room, name='create_room'),
    path('join-room/', views.join_room, name='join_room'),
    path('room/<int:room_id>/', views.room_detail, name='room_detail'),
    path('room/<int:room_id>/leave/', views.leave_room, name='leave_room'),
    path('room/<int:room_id>/transfer/', views.transfer_ownership, name='transfer_ownership'),
    
    # Class work
    path('room/<int:room_id>/create-work/', views.create_classwork, name='create_classwork'),
    path('work/<int:work_id>/edit/', views.edit_classwork, name='edit_classwork'),
    path('work/<int:work_id>/delete/', views.delete_classwork, name='delete_classwork'),
    path('work/<int:work_id>/submit/', views.submit_work, name='submit_work'),
    path('work/<int:work_id>/add-comment/', views.add_stream_comment, name='add_stream_comment'),
    
    # Submissions
    path('submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    
    # Notifications
    path('notifications/api/', views.notification_api, name='notification_api'),
    path('notifications/mark-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Notes
    path('notes/', views.notes_list, name='notes'),
    path('notes/<int:note_id>/delete/', views.delete_note, name='delete_note'),
    path('room/<int:room_id>/schedule/', views.schedule_call, name='schedule_call'),
    path('room/<int:room_id>/delete/', views.delete_room, name='delete_room'),
    
    # ============================================
    # VIDEO CALL & CALENDAR ROUTES
    # ============================================
    path('room/<int:room_id>/schedule-call/', views.schedule_call, name='schedule_call'),
    path('room/<int:room_id>/calendar-data/', views.calendar_data, name='calendar_data'),
    path('room/<int:room_id>/upcoming-calls/', views.upcoming_calls, name='upcoming_calls'),
    path('call/join/<str:jitsi_room_id>/', views.join_call, name='join_call'),
    path('call/<int:call_id>/cancel/', views.cancel_call, name='cancel_call'),
    path('room/<int:room_id>/instant-call/', views.start_instant_call, name='start_instant_call'),
]