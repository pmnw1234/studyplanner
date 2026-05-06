from django.urls import path
from . import views

urlpatterns = [
    path('send/<int:user_id>/', views.send_message, name='send_message'),
    path('get/<int:user_id>/', views.get_messages, name='get_messages'),
    path('conversations/', views.get_conversations, name='get_conversations'),
    path('unread/', views.get_unread_count, name='get_unread_count'),
    path('read/<int:message_id>/', views.mark_as_read, name='mark_as_read'),
    path('read-all/<int:user_id>/', views.mark_all_as_read, name='mark_all_as_read'),
    path('', views.conversation_list_view, name='conversation_list'),
]