from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

# Custom 404 view that works even in debug mode
def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('useraccount.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('feed/', include('feedview.urls')),
    path('profiles/', include('profiles.urls')),
    path('messages/', include('direct_message.urls')),
    path('library/', include('studyroom.urls')),  # ← KEEP ONLY THIS ONE
    # path('studyroom/', include('studyroom.urls')),  ← DELETE/REMOVE THIS LINE
    path('reviews/', include('reviews.urls')),
    path('ai-assistant/', include('ai_assistant.urls')),
    path('Subscription/',include('Subscription.urls')),
]

# Override Django's debug 404
if settings.DEBUG:
    from django.views import debug
    def custom_technical_404_response(request, exception):
        return custom_404_view(request, exception)
    debug.technical_404_response = custom_technical_404_response

# Media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)