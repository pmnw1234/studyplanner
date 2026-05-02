from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import Http404
from django.shortcuts import render

# Custom 404 view that works even in debug mode
def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('useraccount.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('feed/', include('feedview.urls')),  # Keep feedview from feed-view branch
    path('profiles/', include('profiles.urls')),  # Keep profiles from main branch
]

# Add this at the very bottom
if settings.DEBUG:
    # Override Django's default debug 404
    from django.views import debug
    original_technical_404_response = debug.technical_404_response
    def custom_technical_404_response(request, exception):
        return custom_404_view(request, exception)
    debug.technical_404_response = custom_technical_404_response

# Add media URLs
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)