# profiles/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('<int:user_id>/', views.view_other_profile, name='view_other_profile'),
    path('<int:user_id>/connect/', views.send_connection_request, name='send_connection_request'),
    path('<int:user_id>/cancel/', views.cancel_request, name='cancel_request'),
    path('accept/<int:request_id>/', views.accept_connection, name='accept_connection'),
    path('decline/<int:request_id>/', views.decline_connection, name='decline_connection'),
    path('<int:user_id>/unfriend/', views.unfriend_user, name='unfriend_user'),
    path('<int:user_id>/block/', views.block_user, name='block_user'),
    
]