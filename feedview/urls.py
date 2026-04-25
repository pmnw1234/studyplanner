from django.urls import path
from . import views

urlpatterns = [
    path('', views.feed_view, name='feed'),
    path('inbox/', views.inbox_view, name='inbox'),
    path('send/<int:user_id>/', views.send_request, name='send_request'),
    path('accept/<int:request_id>/', views.accept_request, name='accept'),
    path('decline/<int:request_id>/', views.decline_request, name='decline'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),
]