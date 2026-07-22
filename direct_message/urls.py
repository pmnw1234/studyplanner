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
    path('chat/<int:user_id>/', views.chat_view, name='chat_view'),
    path('friends/', views.get_friends, name='get_friends'),
    path('group/create/', views.create_group_chat, name='create_group_chat'),
    path('group-chat/<int:group_id>/', views.group_chat_view, name='group_chat_view'),
    path('group/send/<int:group_id>/', views.send_group_message, name='send_group_message'),
    path('group/get/<int:group_id>/', views.get_group_messages, name='get_group_messages'),
    path('group-chat/<int:group_id>/leave/', views.leave_group_chat, name='leave_group_chat'),
    path('group-chat/<int:group_id>/delete/', views.delete_group_chat, name='delete_group_chat'), 
       
]