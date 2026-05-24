from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
]