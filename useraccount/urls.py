from django.urls import path
from useraccount import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    
    path('',views.register_view,name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/', views.profile_view, name='profile'),
    
]
static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
