from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class SubscriptionPlan(models.Model):
    DURATION_CHOICES = [
        (30, '1 Month'),
        (90, '3 Months'),
        (180, '6 Months'),
        (365, '12 Months'),
    ]
    
    name = models.CharField(max_length=100)
    duration_days = models.IntegerField(choices=DURATION_CHOICES, default=30)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_duration_days_display()}"
    
    def get_price_per_month(self):
        if self.duration_days == 30:
            return self.price
        months = self.duration_days / 30.0
        price_per_month = float(self.price) / months
        return Decimal(str(round(price_per_month, 2)))
    
    def get_discount_percentage(self):
        if self.duration_days == 30:
            return 0
        monthly_price = 5000.00
        price_per_month = float(self.get_price_per_month())
        if monthly_price > 0:
            discount = ((monthly_price - price_per_month) / monthly_price) * 100
            return int(round(discount))
        return 0


class Subscription(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='free'
    )
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan}"
    
    def is_premium(self):
        if self.plan != 'premium' or not self.is_active:
            return False
        if self.end_date and self.end_date < timezone.now():
            return False
        return True
    
    def get_days_remaining(self):
        if not self.is_premium():
            return 0
        if self.end_date:
            delta = self.end_date - timezone.now()
            return max(0, delta.days)
        return 0
    
    def get_status_display(self):
        if self.plan == 'free':
            return 'Free'
        if not self.is_active:
            return 'Inactive'
        if self.is_premium():
            return 'Active'
        if self.end_date and self.end_date < timezone.now():
            return 'Expired'
        return 'Pending'


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('kbz_pay', 'KBZ Pay'),
        ('wave_pay', 'Wave Pay'),
        ('bank_transfer', 'Bank Transfer'),
        ('aya_pay', 'AYA Pay'),
        ('cb_pay', 'CB Pay'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    duration_days = models.IntegerField(default=30)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True
    )
    transaction_id = models.CharField(
        max_length=255,
        blank=True
    )
    screenshot = models.ImageField(
        upload_to='payments/screenshots/%Y/%m/%d/',
        blank=True,
        null=True
    )
    notes = models.TextField(blank=True, help_text="Additional notes from user")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    admin_notes = models.TextField(blank=True, help_text="Admin notes for this payment")
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()} - {self.created_at.strftime('%Y-%m-%d')}"
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    def get_payment_method_display(self):
        return dict(self.PAYMENT_METHOD_CHOICES).get(self.payment_method, self.payment_method)