from django.urls import path
from . import views

urlpatterns = [
    path('library/', views.studyroom_dashboard, name='studyroom_dashboard'),
    path('create-room/', views.create_room, name='create_room'),
    path('join-room/', views.join_room, name='join_room'),
    path('room/<int:room_id>/', views.room_detail, name='room_detail'),
]