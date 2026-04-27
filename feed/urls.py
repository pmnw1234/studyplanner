from django.urls import path
from . import views

urlpatterns = [
    path('', views.feed_view, name='feed'),
    path('create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
]