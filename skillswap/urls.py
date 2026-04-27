
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('useraccount.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('feed/', include('feedview.urls')),  # Keep feedview from feed-view branch
    path('profile/', include('profiles.urls')),  # Keep profiles from main branch
    path('feed/', include('feed.urls')),
]