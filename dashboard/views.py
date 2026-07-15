from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from transactions.models import Transaction
from django.utils import timezone
from datetime import timedelta

@login_required
def home(request):
    # Get user's transactions
    transactions = Transaction.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).order_by('-created_at')
    
    # Calculate stats
    total_transactions = transactions.count()
    
    active_transactions = transactions.filter(
        status__in=['pending_payment', 'payment_confirmed', 'in_progress', 'delivered']
    ).count()
    
    completed_transactions = transactions.filter(status='completed').count()
    
    pending_transactions = transactions.filter(status='pending_payment').count()
    
    disputed_transactions = transactions.filter(status='disputed').count()
    
    # Calculate total volume (completed transactions)
    total_volume = transactions.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Get recent transactions (last 5)
    recent_transactions = transactions[:5]
    
    # Get transactions requiring action
    actions_needed = []
    
    # Buyer needs to pay
    awaiting_payment = transactions.filter(
        buyer=request.user,
        status='pending_payment'
    )
    
    # Seller needs to deliver
    awaiting_delivery = transactions.filter(
        seller=request.user,
        status='payment_confirmed'
    )
    
    # Buyer needs to confirm receipt
    awaiting_confirmation = transactions.filter(
        buyer=request.user,
        status='delivered'
    )
    
    # Disputed transactions
    active_disputes = transactions.filter(
        status='disputed'
    )
    
    # Combine all actions needed
    actions_needed = list(awaiting_payment) + list(awaiting_delivery) + list(awaiting_confirmation)
    
    # Get monthly transaction data for chart (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        month_start = timezone.now() - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        month_transactions = transactions.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        )
        monthly_data.append({
            'month': month_start.strftime('%b'),
            'count': month_transactions.count(),
            'volume': month_transactions.filter(status='completed').aggregate(
                total=Sum('amount')
            )['total'] or 0
        })
    
    # Get recent notifications (placeholder - will be implemented with notification system)
    notifications = [
        {
            'icon': 'fa-info-circle',
            'message': 'Welcome to SecureEscrow Kenya! Complete your profile to get started.',
            'time': 'Just now',
            'unread': True
        }
    ]
    
    if not request.user.is_verified:
        notifications.append({
            'icon': 'fa-shield-alt',
            'message': 'Verify your identity to increase your transaction limits.',
            'time': '2 hours ago',
            'unread': False
        })
    
    if active_transactions == 0 and total_transactions == 0:
        notifications.append({
            'icon': 'fa-exchange-alt',
            'message': 'Start your first secure escrow transaction today!',
            'time': '1 day ago',
            'unread': False
        })
    
    context = {
        'user': request.user,
        'total_transactions': total_transactions,
        'active_transactions': active_transactions,
        'completed_transactions': completed_transactions,
        'pending_transactions': pending_transactions,
        'disputed_transactions': disputed_transactions,
        'total_volume': total_volume,
        'recent_transactions': recent_transactions,
        'actions_needed': actions_needed,
        'awaiting_payment': awaiting_payment,
        'awaiting_delivery': awaiting_delivery,
        'awaiting_confirmation': awaiting_confirmation,
        'active_disputes': active_disputes,
        'monthly_data': monthly_data,
        'notifications': notifications,
    }
    return render(request, 'dashboard/home.html', context)


@login_required
def profile_redirect(request):
    """Redirect to user profile page."""
    return redirect('users:profile')


@login_required
def transaction_summary(request):
    """Get transaction summary as JSON (for AJAX calls)."""
    from django.http import JsonResponse
    
    transactions = Transaction.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    )
    
    # Count by status
    status_counts = {}
    for status in Transaction.STATUS_CHOICES:
        status_counts[status[0]] = transactions.filter(status=status[0]).count()
    
    # Monthly data for charts
    monthly_labels = []
    monthly_values = []
    for i in range(5, -1, -1):
        month_start = timezone.now() - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        count = transactions.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        monthly_labels.append(month_start.strftime('%b %Y'))
        monthly_values.append(count)
    
    data = {
        'status_counts': status_counts,
        'monthly_labels': monthly_labels,
        'monthly_values': monthly_values,
        'total': transactions.count(),
    }
    
    return JsonResponse(data)