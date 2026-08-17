from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.db import transaction
from django.db.models import Count, Sum, Q, Avg
from django.core.paginator import Paginator
from django.urls import reverse
from django.db import models
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import timedelta
from .models import User
from .models import Subscription, Payment, SubscriptionPlan
from useraccount.models import UserProfile, Connection
from feedview.models import Post
from studyroom.models import StudyRoom
from decimal import Decimal

# ============================================
# USER VIEWS
# ============================================

@login_required
def plans(request):
    """Display the plans page with Free and Premium options"""
    subscription = Subscription.objects.filter(user=request.user).first()
    
    if not subscription:
        subscription = Subscription.objects.create(
            user=request.user,
            plan='free',
            is_active=True,
            start_date=timezone.now()
        )
    
    # Get all active subscription plans
    premium_plans = SubscriptionPlan.objects.filter(is_active=True).order_by('duration_days')
    
    # Check if user has pending payment
    pending_payment = Payment.objects.filter(
        user=request.user,
        status='pending'
    ).first()
    
    context = {
        'subscription': subscription,
        'is_premium': subscription.is_premium(),
        'premium_plans': premium_plans,
        'pending_payment': pending_payment,
        'days_remaining': subscription.get_days_remaining(),
    }
    
    return render(request, 'subscription/plans.html', context)


@login_required
def checkout(request):
    """Display the checkout page with duration options"""
    subscription = Subscription.objects.filter(user=request.user).first()
    
    if subscription and subscription.is_premium():
        messages.info(request, "You already have an active Premium subscription!")
        return redirect('my_subscription')
    
    pending_payment = Payment.objects.filter(
        user=request.user,
        status='pending'
    ).first()
    
    if pending_payment:
        messages.warning(request, "You have a pending payment. Please wait for approval.")
        return redirect('my_subscription')
    
    # Get selected plan from query params
    selected_duration = request.GET.get('duration', 30)
    plan = SubscriptionPlan.objects.filter(duration_days=int(selected_duration), is_active=True).first()
    
    if not plan:
        plan = SubscriptionPlan.objects.filter(is_active=True).first()
    
    context = {
        'subscription': subscription,
        'selected_plan': plan,
    }
    
    return render(request, 'subscription/checkout.html', context)


@login_required
def payment(request):
    """Handle payment submission"""
    subscription = Subscription.objects.filter(user=request.user).first()
    
    if subscription and subscription.is_premium():
        messages.info(request, "You already have an active Premium subscription!")
        return redirect('my_subscription')
    
    pending_payment = Payment.objects.filter(
        user=request.user,
        status='pending'
    ).first()
    
    if pending_payment:
        messages.warning(request, "You have a pending payment. Please wait for approval.")
        return redirect('my_subscription')
    
    # Get selected plan from GET or POST
    selected_duration = request.GET.get('duration', 30)
    if request.method == 'POST':
        selected_duration = request.POST.get('duration', 30)
    
    plan = SubscriptionPlan.objects.filter(duration_days=int(selected_duration), is_active=True).first()
    
    if not plan:
        plan = SubscriptionPlan.objects.filter(is_active=True).first()
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        transaction_id = request.POST.get('transaction_id')
        screenshot = request.FILES.get('screenshot')
        notes = request.POST.get('notes', '')
        duration = int(request.POST.get('duration', 30))
        
        # Validate required fields
        if not payment_method:
            messages.error(request, "Please select a payment method.")
            return render(request, 'subscription/payment.html', {
                'error': 'Please select a payment method',
                'selected_plan': plan
            })
        
        if not transaction_id:
            messages.error(request, "Please enter your transaction ID.")
            return render(request, 'subscription/payment.html', {
                'error': 'Please enter your transaction ID',
                'selected_plan': plan
            })
        
        if not screenshot:
            messages.error(request, "Please upload a payment screenshot.")
            return render(request, 'subscription/payment.html', {
                'error': 'Please upload a payment screenshot',
                'selected_plan': plan
            })
        
        try:
            with transaction.atomic():
                # Get or create the plan
                selected_plan = SubscriptionPlan.objects.filter(
                    duration_days=duration,
                    is_active=True
                ).first()
                
                if not selected_plan:
                    selected_plan = SubscriptionPlan.objects.filter(is_active=True).first()
                
                # Create the payment record
                payment = Payment.objects.create(
                    user=request.user,
                    plan=selected_plan,
                    duration_days=duration,
                    amount=selected_plan.price if selected_plan else 5000.00,
                    payment_method=payment_method,
                    transaction_id=transaction_id,
                    notes=notes,
                    status='pending'
                )
                
                # Handle screenshot upload
                if screenshot:
                    payment.screenshot = screenshot
                    payment.save()
                
                messages.success(
                    request, 
                    mark_safe(
                        '✅ Payment submitted successfully! Our team will review it within 24-48 hours. '
                        '<a href="{}" style="color: var(--accent-primary); text-decoration: underline;">View Status</a>'
                    ).format(reverse('my_subscription'))
                )
                
                return redirect('my_subscription')
                
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'subscription/payment.html', {
                'error': str(e),
                'selected_plan': plan
            })
    
    context = {
        'subscription': subscription,
        'selected_plan': plan,
    }
    
    return render(request, 'subscription/payment.html', context)


@login_required
def my_subscription(request):
    """Display the user's subscription details with status"""
    subscription = Subscription.objects.filter(user=request.user).first()
    
    if not subscription:
        subscription = Subscription.objects.create(
            user=request.user,
            plan='free',
            is_active=True,
            start_date=timezone.now()
        )
    
    # Check for pending payments
    pending_payment = Payment.objects.filter(
        user=request.user,
        status='pending'
    ).first()
    
    # Get recent payments
    recent_payments = Payment.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Calculate days remaining
    days_remaining = subscription.get_days_remaining()
    
    # Get status
    status = subscription.get_status_display()
    status_class = 'active' if subscription.is_premium() else 'inactive'
    if pending_payment:
        status = 'Pending Approval'
        status_class = 'pending'
    
    context = {
        'subscription': subscription,
        'is_premium': subscription.is_premium(),
        'days_remaining': days_remaining,
        'pending_payment': pending_payment,
        'recent_payments': recent_payments,
        'status': status,
        'status_class': status_class,
    }
    
    return render(request, 'subscription/my_subscription.html', context)


@login_required
def payment_history(request):
    """Display user's payment history"""
    payments = Payment.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'payments': page_obj,
    }
    
    return render(request, 'subscription/payment_history.html', context)


# ============================================
# ADMIN VIEWS
# ============================================
def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard with overview statistics"""
    
    # ============================================
    # USER STATISTICS
    # ============================================
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    
    # Users joined this week
    week_ago = timezone.now() - timedelta(days=7)
    new_users_week = User.objects.filter(date_joined__gte=week_ago).count()
    
    # Users joined this month
    month_ago = timezone.now() - timedelta(days=30)
    new_users_month = User.objects.filter(date_joined__gte=month_ago).count()
    
    # ============================================
    # SUBSCRIPTION STATISTICS
    # ============================================
    total_premium = Subscription.objects.filter(plan='premium', is_active=True).count()
    total_free = Subscription.objects.filter(plan='free', is_active=True).count()
    expired_subscriptions = Subscription.objects.filter(
        plan='premium',
        is_active=True,
        end_date__lt=timezone.now()
    ).count()
    
    # ============================================
    # PAYMENT STATISTICS
    # ============================================
    pending_payments = Payment.objects.filter(status='pending').count()
    approved_payments = Payment.objects.filter(status='approved').count()
    rejected_payments = Payment.objects.filter(status='rejected').count()
    total_payments = Payment.objects.count()
    total_revenue = Payment.objects.filter(status='approved').aggregate(
        Sum('amount')
    )['amount__sum'] or Decimal('0.00')
    
    # Recent payments
    recent_payments = Payment.objects.all().order_by('-created_at')[:10]
    
    # Monthly revenue (last 6 months)
    monthly_revenue = []
    for i in range(6, 0, -1):
        month_start = timezone.now() - timedelta(days=30 * i)
        month_end = timezone.now() - timedelta(days=30 * (i - 1))
        revenue = Payment.objects.filter(
            status='approved',
            approved_at__gte=month_start,
            approved_at__lt=month_end
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        monthly_revenue.append({
            'month': month_start.strftime('%b'),
            'revenue': float(revenue)
        })
    
    # ============================================
    # STUDY ROOM STATISTICS - FIXED (No RoomMember)
    # ============================================
    total_rooms = StudyRoom.objects.count()
    
    # Calculate total memberships from the ManyToMany field
    total_memberships = 0
    for room in StudyRoom.objects.all():
        total_memberships += room.members.count()
    
    # Include creator in member count for each room
    total_memberships_with_creators = total_memberships + total_rooms
    
    # Average members per room (including creator)
    avg_members_per_room = total_memberships_with_creators / total_rooms if total_rooms > 0 else 0
    
    # Get rooms with most members - FIXED: Use Count from django.db.models
    from django.db.models import Count
    top_rooms = StudyRoom.objects.annotate(
        member_count=Count('members')
    ).order_by('-member_count')[:5]
    
    # ============================================
    # POST STATISTICS
    # ============================================
    total_posts = Post.objects.count()
    posts_week = Post.objects.filter(created_at__gte=week_ago).count()
    
    # ============================================
    # RECENT ACTIVITY - COMBINED
    # ============================================
    recent_users = User.objects.all().order_by('-date_joined')[:5]
    recent_posts = Post.objects.all().order_by('-created_at')[:5]
    
    context = {
        # User stats
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'superusers': superusers,
        'new_users_week': new_users_week,
        'new_users_month': new_users_month,
        
        # Subscription stats
        'total_premium': total_premium,
        'total_free': total_free,
        'expired_subscriptions': expired_subscriptions,
        
        # Payment stats
        'pending_payments': pending_payments,
        'approved_payments': approved_payments,
        'rejected_payments': rejected_payments,
        'total_payments': total_payments,
        'total_revenue': total_revenue,
        'recent_payments': recent_payments,
        'monthly_revenue': monthly_revenue,
        
        # Room stats - FIXED
        'total_rooms': total_rooms,
        'total_memberships': total_memberships_with_creators,
        'avg_members_per_room': round(avg_members_per_room, 1),
        'top_rooms': top_rooms,
        
        # Post stats
        'total_posts': total_posts,
        'posts_week': posts_week,
        
        # Recent activity
        'recent_users': recent_users,
        'recent_posts': recent_posts,
        
        # Current time for display
        'now': timezone.now(),
    }
    
    return render(request, 'admin/admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_users(request):
    """Admin view to manage users"""
    users = User.objects.all().order_by('-date_joined')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Filter
    filter_type = request.GET.get('filter', '')
    if filter_type == 'staff':
        users = users.filter(is_staff=True)
    elif filter_type == 'superuser':
        users = users.filter(is_superuser=True)
    elif filter_type == 'active':
        users = users.filter(is_active=True)
    elif filter_type == 'inactive':
        users = users.filter(is_active=False)
    elif filter_type == 'premium':
        premium_user_ids = Subscription.objects.filter(plan='premium', is_active=True).values_list('user_id', flat=True)
        users = users.filter(id__in=premium_user_ids)
    elif filter_type == 'free':
        free_user_ids = Subscription.objects.filter(plan='free', is_active=True).values_list('user_id', flat=True)
        users = users.filter(id__in=free_user_ids)
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,  # ← Pass users directly, not as a list of dicts
        'search_query': search_query,
        'filter_type': filter_type,
        'total_users': User.objects.count(),
        'total_premium': Subscription.objects.filter(plan='premium', is_active=True).count(),
        'total_free': Subscription.objects.filter(plan='free', is_active=True).count(),
        'now': timezone.now(),
    }
    
    return render(request, 'admin/admin_users.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_detail(request, user_id):
    """Admin view for user details"""
    user = get_object_or_404(User, id=user_id)
    profile = UserProfile.objects.filter(user=user).first()
    subscription = Subscription.objects.filter(user=user).first()
    payments = Payment.objects.filter(user=user).order_by('-created_at')[:10]
    
    context = {
        'user': user,
        'profile': profile,
        'subscription': subscription,
        'payments': payments,
    }
    
    return render(request, 'admin/admin_user_detail.html', context)


@login_required
@user_passes_test(is_admin)
def admin_toggle_user_status(request, user_id):
    """Admin toggle user active status"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user == request.user:
            messages.error(request, "You cannot deactivate yourself!")
        else:
            user.is_active = not user.is_active
            user.save()
            status = "activated" if user.is_active else "deactivated"
            messages.success(request, f"User {user.username} has been {status}.")
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin)
def admin_toggle_staff_status(request, user_id):
    """Admin toggle staff status"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user == request.user:
            messages.error(request, "You cannot change your own staff status!")
        else:
            user.is_staff = not user.is_staff
            user.save()
            status = "granted" if user.is_staff else "revoked"
            messages.success(request, f"Staff status {status} for {user.username}.")
    return redirect('admin_users')


@login_required
@user_passes_test(is_admin)
def admin_delete_user(request, user_id):
    """Admin delete user"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user == request.user:
            messages.error(request, "You cannot delete yourself!")
        else:
            username = user.username
            user.delete()
            messages.success(request, f"User {username} has been deleted.")
    return redirect('admin_users')

@login_required
def admin_payments(request):
    """Admin view to manage all payments"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to view this page.")
        return redirect('dashboard')
    
    # Get counts
    pending_count = Payment.objects.filter(status='pending').count()
    approved_count = Payment.objects.filter(status='approved').count()
    rejected_count = Payment.objects.filter(status='rejected').count()
    total_count = Payment.objects.count()
    
    # Get all payments with filters
    status_filter = request.GET.get('status', '')
    payments = Payment.objects.all().order_by('-created_at')
    
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'payments': page_obj,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_count': total_count,
        'status_filter': status_filter,
    }
    
    return render(request, 'subscription/admin_payments.html', context)


@login_required
@user_passes_test(is_admin)
def view_payment(request, payment_id):
    """View payment details (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    data = {
        'id': payment.id,
        'user': payment.user.username,
        'user_id': payment.user.id,
        'plan': payment.plan.name if payment.plan else 'Premium',
        'duration_days': payment.duration_days,
        'amount': str(payment.amount),
        'payment_method': payment.get_payment_method_display(),
        'transaction_id': payment.transaction_id,
        'screenshot_url': payment.screenshot.url if payment.screenshot and payment.screenshot else None,
        'notes': payment.notes or '',
        'admin_notes': payment.admin_notes or '',
        'status': payment.status,
        'status_display': payment.get_status_display(),
        'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M'),
        'approved_at': payment.approved_at.strftime('%Y-%m-%d %H:%M') if payment.approved_at else None,
        'rejected_at': payment.rejected_at.strftime('%Y-%m-%d %H:%M') if payment.rejected_at else None,
    }
    
    return JsonResponse(data)


@login_required
@transaction.atomic
def approve_payment(request, payment_id):
    """Admin view to approve a payment"""
    if not request.user.is_staff:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('admin_payments')
    
    try:
        payment = Payment.objects.get(id=payment_id, status='pending')
        
        # Update payment status
        payment.status = 'approved'
        payment.approved_at = timezone.now()
        payment.save()
        
        # Get the duration days from the payment
        duration_days = payment.duration_days or 30
        
        # Activate or extend premium subscription
        subscription, created = Subscription.objects.get_or_create(
            user=payment.user,
            defaults={
                'plan': 'premium',
                'is_active': True,
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=duration_days)
            }
        )
        
        if not created:
            # Extend existing subscription
            subscription.plan = 'premium'
            subscription.is_active = True
            
            if subscription.end_date and subscription.end_date > timezone.now():
                # Extend from current end date
                subscription.end_date = subscription.end_date + timedelta(days=duration_days)
            else:
                # Start new subscription
                subscription.start_date = timezone.now()
                subscription.end_date = timezone.now() + timedelta(days=duration_days)
            
            subscription.save()
        
        messages.success(
            request, 
            f"✅ Payment #{payment.id} approved successfully! {payment.user.username} is now a premium user."
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Payment approved successfully'})
        
        return redirect('admin_payments')
        
    except Payment.DoesNotExist:
        messages.error(request, "Payment not found.")
        return redirect('admin_payments')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('admin_payments')


@login_required
@transaction.atomic
def reject_payment(request, payment_id):
    """Admin view to reject a payment"""
    if not request.user.is_staff:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('admin_payments')
    
    try:
        payment = Payment.objects.get(id=payment_id, status='pending')
        payment.status = 'rejected'
        payment.rejected_at = timezone.now()
        payment.save()
        
        messages.warning(
            request, 
            f"Payment #{payment.id} rejected. User has been notified."
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Payment rejected'})
        
        return redirect('admin_payments')
        
    except Payment.DoesNotExist:
        messages.error(request, "Payment not found.")
        return redirect('admin_payments')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('admin_payments')