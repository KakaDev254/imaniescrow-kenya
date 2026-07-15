from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponseForbidden
from datetime import timedelta
from .models import Transaction, TransactionMessage, TransactionMilestone
from .forms import (
    TransactionForm, TransactionMessageForm,
    ConfirmDeliveryForm, ConfirmReceiptForm, DisputeForm
)
from users.models import CustomUser

@login_required
def transaction_list(request):
    """Display all transactions for the current user."""
    transactions = Transaction.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).order_by('-created_at')
    
    # Filter by status if specified
    status_filter = request.GET.get('status')
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    context = {
        'transactions': transactions,
        'status_filter': status_filter,
        'active_count': transactions.filter(
            status__in=['pending_payment', 'payment_confirmed', 'in_progress', 'delivered']
        ).count(),
        'completed_count': transactions.filter(status='completed').count(),
        'disputed_count': transactions.filter(status='disputed').count(),
    }
    return render(request, 'transactions/list.html', context)


@login_required
def create_transaction(request):
    """Create a new escrow transaction."""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.buyer = request.user
            
            # Calculate escrow fee
            transaction.escrow_fee = transaction.calculate_escrow_fee()
            transaction.total_amount = transaction.amount + transaction.escrow_fee
            
            # Set status
            transaction.status = 'pending_payment'
            
            # Set delivery deadline
            transaction.delivery_deadline = timezone.now() + timedelta(days=14)
            
            transaction.save()
            
            # Create milestone
            TransactionMilestone.objects.create(
                transaction=transaction,
                milestone_type='created',
                description=f'Transaction created by {request.user.get_full_name()}',
                created_by=request.user
            )
            
            messages.success(
                request,
                f'Transaction created successfully! Your Transaction ID is {transaction.transaction_id}'
            )
            return redirect('transactions:detail', transaction_id=transaction.transaction_id)
    else:
        form = TransactionForm()
    
    context = {
        'form': form,
        'escrow_fee_percentage': '2%',  # This can be dynamic based on amount
    }
    return render(request, 'transactions/create.html', context)


@login_required
def transaction_detail(request, transaction_id):
    """Display transaction details."""
    transaction = get_object_or_404(
        Transaction.objects.filter(
            Q(buyer=request.user) | Q(seller=request.user),
            transaction_id=transaction_id
        )
    )
    
    # Get messages
    transaction_messages = transaction.messages.all()
    
    # Get milestones
    milestones = transaction.milestones.all()
    
    # Handle message form
    if request.method == 'POST' and 'send_message' in request.POST:
        message_form = TransactionMessageForm(request.POST, request.FILES)
        if message_form.is_valid():
            message = message_form.save(commit=False)
            message.transaction = transaction
            message.sender = request.user
            message.save()
            messages.success(request, 'Message sent successfully!')
            return redirect('transactions:detail', transaction_id=transaction_id)
    else:
        message_form = TransactionMessageForm()
    
    context = {
        'transaction': transaction,
        'messages_list': transaction_messages,
        'milestones': milestones,
        'message_form': message_form,
        'is_buyer': request.user == transaction.buyer,
        'is_seller': request.user == transaction.seller,
    }
    return render(request, 'transactions/detail.html', context)


@login_required
def confirm_payment(request, transaction_id):
    """Confirm payment for a transaction."""
    transaction = get_object_or_404(
        Transaction,
        transaction_id=transaction_id,
        buyer=request.user
    )
    
    if transaction.status == 'pending_payment':
        # Simulate payment confirmation (in production, this would verify with M-PESA)
        transaction.status = 'payment_confirmed'
        transaction.payment_date = timezone.now()
        transaction.payment_reference = f"PAY{timezone.now().strftime('%Y%m%d%H%M%S')}"
        transaction.save()
        
        # Create milestone
        TransactionMilestone.objects.create(
            transaction=transaction,
            milestone_type='payment_received',
            description=f'Payment of KES {transaction.total_amount} confirmed',
            created_by=request.user
        )
        
        messages.success(request, 'Payment confirmed! The seller can now proceed with delivery.')
    else:
        messages.error(request, 'Payment cannot be confirmed at this stage.')
    
    return redirect('transactions:detail', transaction_id=transaction_id)


@login_required
def confirm_delivery(request, transaction_id):
    """Seller confirms delivery."""
    transaction = get_object_or_404(
        Transaction,
        transaction_id=transaction_id,
        seller=request.user
    )
    
    if request.method == 'POST':
        form = ConfirmDeliveryForm(request.POST)
        if form.is_valid() and transaction.status == 'payment_confirmed':
            transaction.seller_delivery_confirmation = True
            transaction.status = 'delivered'
            transaction.inspection_deadline = timezone.now() + timedelta(
                days=transaction.inspection_period_days
            )
            transaction.save()
            
            # Create milestone
            TransactionMilestone.objects.create(
                transaction=transaction,
                milestone_type='delivery_confirmed',
                description=f'Delivery confirmed by seller. Inspection period starts.',
                created_by=request.user
            )
            
            messages.success(
                request,
                f'Delivery confirmed! The buyer has {transaction.inspection_period_days} days to inspect.'
            )
            return redirect('transactions:detail', transaction_id=transaction_id)
    else:
        form = ConfirmDeliveryForm()
    
    context = {
        'transaction': transaction,
        'form': form,
    }
    return render(request, 'transactions/confirm_delivery.html', context)


@login_required
def confirm_receipt(request, transaction_id):
    """Buyer confirms receipt and satisfaction."""
    transaction = get_object_or_404(
        Transaction,
        transaction_id=transaction_id,
        buyer=request.user
    )
    
    if request.method == 'POST':
        form = ConfirmReceiptForm(request.POST)
        if form.is_valid() and transaction.status == 'delivered':
            transaction.buyer_receipt_confirmation = True
            
            if form.cleaned_data.get('satisfied'):
                # Buyer is satisfied - complete transaction
                transaction.buyer_satisfaction_confirmation = True
                transaction.status = 'completed'
                transaction.completed_at = timezone.now()
                transaction.save()
                
                # Create milestone
                TransactionMilestone.objects.create(
                    transaction=transaction,
                    milestone_type='buyer_accepted',
                    description=f'Buyer accepted and funds released to seller',
                    created_by=request.user
                )
                
                # In production: Release funds to seller's M-PESA account
                messages.success(
                    request,
                    'Thank you! Funds will be released to the seller.'
                )
            else:
                transaction.save()
                messages.info(
                    request,
                    'Receipt confirmed. You can accept the transaction when satisfied.'
                )
            
            return redirect('transactions:detail', transaction_id=transaction_id)
    else:
        form = ConfirmReceiptForm()
    
    context = {
        'transaction': transaction,
        'form': form,
    }
    return render(request, 'transactions/confirm_receipt.html', context)


@login_required
def raise_dispute(request, transaction_id):
    """Raise a dispute for a transaction."""
    transaction = get_object_or_404(
        Transaction.objects.filter(
            Q(buyer=request.user) | Q(seller=request.user),
            transaction_id=transaction_id
        )
    )
    
    if request.method == 'POST':
        form = DisputeForm(request.POST, request.FILES)
        if form.is_valid():
            transaction.is_disputed = True
            transaction.status = 'disputed'
            transaction.dispute_reason = form.cleaned_data['reason']
            transaction.save()
            
            # Create milestone
            TransactionMilestone.objects.create(
                transaction=transaction,
                milestone_type='dispute_raised',
                description=f'Dispute raised: {form.cleaned_data["reason"][:100]}',
                created_by=request.user
            )
            
            messages.warning(
                request,
                'Dispute raised. Our team will review and contact both parties within 24 hours.'
            )
            return redirect('transactions:detail', transaction_id=transaction_id)
    else:
        form = DisputeForm()
    
    context = {
        'transaction': transaction,
        'form': form,
    }
    return render(request, 'transactions/raise_dispute.html', context)


@login_required
def cancel_transaction(request, transaction_id):
    """Cancel a transaction."""
    transaction = get_object_or_404(
        Transaction.objects.filter(
            Q(buyer=request.user) | Q(seller=request.user),
            transaction_id=transaction_id
        )
    )
    
    if transaction.status in ['draft', 'pending_payment']:
        if request.method == 'POST':
            reason = request.POST.get('cancellation_reason', '')
            transaction.status = 'cancelled'
            transaction.cancelled_by = request.user
            transaction.cancellation_reason = reason
            transaction.cancelled_at = timezone.now()
            transaction.save()
            
            # Create milestone
            TransactionMilestone.objects.create(
                transaction=transaction,
                milestone_type='cancelled',
                description=f'Transaction cancelled by {request.user.get_full_name()}: {reason}',
                created_by=request.user
            )
            
            messages.success(request, 'Transaction cancelled successfully.')
            return redirect('transactions:list')
        
        context = {'transaction': transaction}
        return render(request, 'transactions/cancel.html', context)
    else:
        messages.error(request, 'This transaction cannot be cancelled at this stage.')
        return redirect('transactions:detail', transaction_id=transaction_id)