from django.urls import path
from . import views

urlpatterns = [

    path('plans/', views.plans, name='plans'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/', views.payment, name='payment'),
    path('my-subscription/', views.my_subscription, name='my_subscription'),
    path('payment-history/', views.payment_history, name='payment_history'),
    
    # Admin URLs for managing payments
    path('admin-payments/', views.admin_payments, name='admin_payments'),
    path('admin-payment/<int:payment_id>/approve/', views.approve_payment, name='approve_payment'),
    path('admin-payment/<int:payment_id>/reject/', views.reject_payment, name='reject_payment'),
    path('admin-payment/<int:payment_id>/view/', views.view_payment, name='view_payment'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-users/', views.admin_users, name='admin_users'),
    path('admin-user/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin-user/<int:user_id>/toggle-status/', views.admin_toggle_user_status, name='admin_toggle_user_status'),
    path('admin-user/<int:user_id>/toggle-staff/', views.admin_toggle_staff_status, name='admin_toggle_staff_status'),
    path('admin-user/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
]