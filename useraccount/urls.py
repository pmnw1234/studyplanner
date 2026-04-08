from django.urls import path
from useraccount import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Landing page as the home screen
    path('', views.landing_view, name='landing'),
    
    # Account paths
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile paths
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
]

# This part is crucial for showing profile pictures or uploaded files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)