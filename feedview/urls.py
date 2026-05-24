from django.urls import path
from . import views

urlpatterns = [
    path('', views.feed_view, name='feed'),
    path('inbox/', views.inbox_view, name='inbox'),
    path('send/<int:user_id>/', views.send_request, name='send_request'),
    path('accept/<int:request_id>/', views.accept_request, name='accept'),
    path('decline/<int:request_id>/', views.decline_request, name='decline'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/interest/', views.interested_post, name='interested_post'),
    path('post/<int:post_id>/comment/', views.comment_post, name='comment_post'),
    path('post/<int:post_id>/activity/', views.post_activity, name='post_activity'),
    path('notification/reply/<int:activity_id>/', views.send_reply_view, name='send_reply'),
]