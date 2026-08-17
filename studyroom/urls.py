# studyplanner/studyroom/urls.py

from django.urls import path
from . import views

app_name = 'studyroom'  # Keep this only once

urlpatterns = [
    path('library/', views.studyroom_dashboard, name='studyroom_dashboard'),
    path('create-room/', views.create_room, name='create_room'),
    path('join-room/', views.join_room, name='join_room'),
    path('room/<int:room_id>/', views.room_detail, name='room_detail'),
    path('room/<int:room_id>/create-work/', views.create_classwork, name='create_classwork'),
    path('work/<int:work_id>/edit/', views.edit_classwork, name='edit_classwork'),
    path('work/<int:work_id>/delete/', views.delete_classwork, name='delete_classwork'),
    path('work/<int:work_id>/submit/', views.submit_work, name='submit_work'),
    path('submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    path('room/<int:room_id>/leave/', views.leave_room, name='leave_room'),
    path('room/<int:room_id>/transfer/', views.transfer_ownership, name='transfer_ownership'),
    path('work/<int:work_id>/add-comment/', views.add_stream_comment, name='add_stream_comment'),
    path('notifications/api/', views.notification_api, name='notification_api'),
    path('notifications/mark-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notes/', views.notes_list, name='notes'),
    path('notes/<int:note_id>/delete/', views.delete_note, name='delete_note'),
    path('room/<int:room_id>/schedule/', views.schedule_call, name='schedule_call'),
    path('room/<int:room_id>/delete/', views.delete_room, name='delete_room'),
]