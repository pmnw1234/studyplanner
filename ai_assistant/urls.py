# ai_assistant/urls.py
from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('', views.ai_assistant_dashboard, name='dashboard'),
    path('chat/', views.ai_chat_api, name='chat_api'),
    path('tip/', views.get_study_tip_api, name='get_tip'),
    path('quote/', views.get_motivational_quote_api, name='get_quote'),
    path('clear/', views.clear_conversation, name='clear_conversation'),
]