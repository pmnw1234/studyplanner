from django.urls import path
from useraccount import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.landing_view, name='landing'),  # Landing page as root
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('post/<int:post_id>/interest/', views.interest_post, name='interest_post'),
    path('post/<int:post_id>/comment/', views.comment_post, name='comment_post'),
    path('certification/add/', views.add_certification, name='add_certification'),
    path('certification/edit/<int:cert_id>/', views.edit_certification, name='edit_certification'),
    path('certification/delete/<int:cert_id>/', views.delete_certification, name='delete_certification'),
    
    # ===== NEW URLS FOR CONNECTIONS =====
    path('profile/<int:user_id>/', views.view_other_profile, name='view_other_profile'),
    path('connect/<int:user_id>/', views.connect_user, name='connect_user'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)