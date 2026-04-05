from django.urls import path
from useraccount import views

urlpatterns = [
    path('',views.register_view,name='register'),
]