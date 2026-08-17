from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import SubscriptionPlan, Subscription, Payment

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_days', 'price', 'is_active']
    list_filter = ['is_active', 'duration_days']
    search_fields = ['name', 'description']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'is_active', 'start_date', 'end_date', 'days_remaining']
    list_filter = ['plan', 'is_active']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def days_remaining(self, obj):
        if not obj.is_premium():
            return '-'
        if obj.end_date:
            delta = obj.end_date - timezone.now()
            return max(0, delta.days)
        return '-'
    days_remaining.short_description = 'Days Remaining'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan_name', 'amount', 'payment_method_display', 'status_display', 'created_at', 'action_buttons']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__username', 'transaction_id', 'user__email']
    readonly_fields = ['created_at', 'approved_at', 'rejected_at']
    list_per_page = 20
    actions = ['approve_payments', 'reject_payments']
    
    def plan_name(self, obj):
        return obj.plan.name if obj.plan else 'Premium'
    plan_name.short_description = 'Plan'
    
    def payment_method_display(self, obj):
        return obj.get_payment_method_display()
    payment_method_display.short_description = 'Payment Method'
    
    def status_display(self, obj):
        colors = {
            'pending': '#f59e0b',
            'approved': '#10b981',
            'rejected': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def action_buttons(self, obj):
        if obj.status == 'pending':
            approve_url = reverse('admin:approve_payment', args=[obj.id])
            reject_url = reverse('admin:reject_payment', args=[obj.id])
            return format_html(
                '<a href="{}" style="background: #10b981; color: white; padding: 4px 12px; border-radius: 4px; text-decoration: none; margin-right: 5px;">Approve</a>'
                '<a href="{}" style="background: #ef4444; color: white; padding: 4px 12px; border-radius: 4px; text-decoration: none;">Reject</a>',
                approve_url, reject_url
            )
        return '-'
    action_buttons.short_description = 'Actions'
    
    def approve_payments(self, request, queryset):
        for payment in queryset.filter(status='pending'):
            payment.status = 'approved'
            payment.approved_at = timezone.now()
            payment.save()
            
            # Activate subscription
            subscription, created = Subscription.objects.get_or_create(
                user=payment.user,
                defaults={
                    'plan': 'premium',
                    'is_active': True,
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timezone.timedelta(days=payment.duration_days or 30)
                }
            )
            if not created:
                subscription.plan = 'premium'
                subscription.is_active = True
                if subscription.end_date and subscription.end_date > timezone.now():
                    subscription.end_date = subscription.end_date + timezone.timedelta(days=payment.duration_days or 30)
                else:
                    subscription.start_date = timezone.now()
                    subscription.end_date = timezone.now() + timezone.timedelta(days=payment.duration_days or 30)
                subscription.save()
        
        self.message_user(request, f"{queryset.filter(status='approved').count()} payments approved.")
    approve_payments.short_description = "Approve selected payments"
    
    def reject_payments(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='rejected', rejected_at=timezone.now())
        self.message_user(request, f"{updated} payments rejected.")
    reject_payments.short_description = "Reject selected payments"
# Register your models here.
