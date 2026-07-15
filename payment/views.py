from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from transactions.models import Transaction
from .models import MpesaPayment, MpesaConfig, EscrowBalance
from .services import MpesaService, MpesaTestHelper

# Create service instance
mpesa_service = MpesaService()

@login_required
def deposit_funds(request):
    """Deposit funds to escrow account."""
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '')
        amount = request.POST.get('amount', '0')
        
        try:
            amount = float(amount)
            if amount < 10:
                messages.error(request, 'Minimum deposit is KES 10.')
                return redirect('payment:deposit')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount.')
            return redirect('payment:deposit')
        
        # Use user's phone if not provided
        if not phone_number:
            phone_number = request.user.phone_number
        
        if not phone_number:
            messages.error(request, 'Please enter a phone number.')
            return redirect('payment:deposit')
        
        # Initiate STK Push
        try:
            result = mpesa_service.initiate_stk_push(
                phone_number=phone_number,
                amount=amount,
                payment_type='deposit',
                user=request.user,
                description='Deposit to SecureEscrow'
            )
            
            if result['success']:
                # Store payment ID in session for confirmation
                request.session['pending_payment_id'] = result['payment_id']
                request.session['payment_reference'] = result['payment_reference']
                
                messages.success(request, result['message'])
                return redirect('payment:confirm_deposit', payment_id=result['payment_id'])
            else:
                messages.error(request, result.get('message', 'Payment failed'))
        except Exception as e:
            messages.error(request, f'Payment error: {str(e)}')
        
        return redirect('payment:deposit')
    
    # GET request - show form
    try:
        escrow_balance, created = EscrowBalance.objects.get_or_create(user=request.user)
    except:
        escrow_balance = None
    
    try:
        payments = MpesaPayment.objects.filter(
            user=request.user,
            payment_type='deposit'
        ).order_by('-created_at')[:10]
    except:
        payments = []
    
    test_numbers = MpesaTestHelper.get_test_phone_numbers()
    
    context = {
        'payments': payments,
        'escrow_balance': escrow_balance,
        'test_mode': True,  # Default to test mode
        'test_numbers': test_numbers,
    }
    return render(request, 'payment/deposit.html', context)


@login_required
def confirm_deposit(request, payment_id):
    """Confirm deposit payment."""
    
    try:
        payment = get_object_or_404(MpesaPayment, id=payment_id, user=request.user)
    except:
        messages.error(request, 'Payment not found.')
        return redirect('payment:deposit')
    
    # Check if already completed
    if payment.status == 'completed':
        messages.info(request, 'Payment was already confirmed.')
        return redirect('payment:deposit')
    
    # Confirm payment
    try:
        result = mpesa_service.confirm_payment(str(payment_id))
        
        if result['success']:
            deposit_result = mpesa_service.process_deposit(payment)
            
            if deposit_result['success']:
                messages.success(request, f'Deposit successful! Receipt: {result.get("mpesa_receipt_number", "N/A")}')
                request.session.pop('pending_payment_id', None)
                request.session.pop('payment_reference', None)
                return redirect('payment:deposit_success', payment_id=payment_id)
    except Exception as e:
        messages.error(request, f'Confirmation error: {str(e)}')
    
    messages.error(request, 'Payment confirmation failed.')
    return redirect('payment:deposit')


@login_required
def deposit_success(request, payment_id):
    """Show deposit success page."""
    payment = get_object_or_404(MpesaPayment, id=payment_id, user=request.user)
    
    try:
        escrow_balance, created = EscrowBalance.objects.get_or_create(user=request.user)
    except:
        escrow_balance = None
    
    context = {
        'payment': payment,
        'escrow_balance': escrow_balance,
    }
    return render(request, 'payment/deposit_success.html', context)


@login_required
def withdraw_funds(request):
    """Withdraw funds to M-PESA."""
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', request.user.phone_number)
        amount = request.POST.get('amount', '0')
        
        try:
            amount = float(amount)
            if amount < 10:
                messages.error(request, 'Minimum withdrawal is KES 10.')
                return redirect('payment:withdraw')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount.')
            return redirect('payment:withdraw')
        
        # Check balance
        try:
            escrow_balance, created = EscrowBalance.objects.get_or_create(user=request.user)
            
            if escrow_balance.available_balance < amount:
                messages.error(request, f'Insufficient balance. Available: KES {escrow_balance.available_balance}')
                return redirect('payment:withdraw')
        except:
            messages.error(request, 'Could not verify balance.')
            return redirect('payment:withdraw')
        
        # Create withdrawal
        try:
            result = mpesa_service.initiate_stk_push(
                phone_number=phone_number,
                amount=amount,
                payment_type='withdrawal',
                user=request.user,
                description='Withdrawal from SecureEscrow'
            )
            
            if result['success']:
                payment = MpesaPayment.objects.get(id=result['payment_id'])
                payment.status = 'completed'
                payment.result_code = '0'
                payment.result_description = 'Withdrawal processed (TEST MODE)'
                payment.mpesa_receipt_number = f"WITHDRAW{timezone.now().strftime('%Y%m%d%H%M')}"
                payment.completed_at = timezone.now()
                payment.save()
                
                mpesa_service.process_withdrawal(payment)
                
                messages.success(request, f'Withdrawal successful! KES {amount} sent to {phone_number}')
                return redirect('payment:withdraw_success', payment_id=result['payment_id'])
        except Exception as e:
            messages.error(request, f'Withdrawal error: {str(e)}')
        
        return redirect('payment:withdraw')
    
    # GET request
    try:
        escrow_balance, created = EscrowBalance.objects.get_or_create(user=request.user)
    except:
        escrow_balance = None
    
    try:
        withdrawals = MpesaPayment.objects.filter(
            user=request.user,
            payment_type='withdrawal'
        ).order_by('-created_at')[:10]
    except:
        withdrawals = []
    
    context = {
        'escrow_balance': escrow_balance,
        'withdrawals': withdrawals,
        'test_mode': True,
    }
    return render(request, 'payment/withdraw.html', context)


@login_required
def withdraw_success(request, payment_id):
    """Show withdrawal success page."""
    payment = get_object_or_404(MpesaPayment, id=payment_id, user=request.user)
    
    try:
        escrow_balance, created = EscrowBalance.objects.get_or_create(user=request.user)
    except:
        escrow_balance = None
    
    context = {
        'payment': payment,
        'escrow_balance': escrow_balance,
    }
    return render(request, 'payment/withdraw_success.html', context)


@login_required
def payment_history(request):
    """Show payment history."""
    try:
        payments = MpesaPayment.objects.filter(
            user=request.user
        ).order_by('-created_at')
    except:
        payments = []
    
    context = {
        'payments': payments,
    }
    return render(request, 'payment/history.html', context)


@csrf_exempt
def mpesa_callback(request):
    """Receive M-PESA payment callbacks."""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            
            checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
            result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            
            try:
                payment = MpesaPayment.objects.get(checkout_request_id=checkout_request_id)
                payment.result_code = str(result_code)
                
                if result_code == 0:
                    payment.status = 'completed'
                    payment.result_description = 'Payment successful'
                    payment.completed_at = timezone.now()
                    payment.save()
                    
                    if payment.payment_type == 'deposit':
                        mpesa_service.process_deposit(payment)
                    elif payment.payment_type == 'withdrawal':
                        mpesa_service.process_withdrawal(payment)
                else:
                    payment.status = 'failed'
                    payment.save()
            except MpesaPayment.DoesNotExist:
                pass
            
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Accepted'})
        except Exception as e:
            return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)})
    
    return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid request'})

@login_required
def simulate_payment_callback(request, payment_id):
    """Simulate M-PESA callback for testing."""
    
    payment = get_object_or_404(MpesaPayment, id=payment_id)
    
    # Only allow in test mode
    if not mpesa_service.test_mode:
        messages.error(request, 'Callbacks are automatically handled in production mode.')
        return redirect('dashboard:home')
    
    # Simulate successful callback
    payment.status = 'completed'
    payment.result_code = '0'
    payment.result_description = 'Callback received - Payment successful (SIMULATED)'
    payment.mpesa_receipt_number = f"SIM{timezone.now().strftime('%Y%m%d%H%M%S')}"
    payment.completed_at = timezone.now()
    payment.save()
    
    if payment.payment_type == 'deposit':
        mpesa_service.process_deposit(payment)
    elif payment.payment_type == 'withdrawal':
        mpesa_service.process_withdrawal(payment)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Callback simulated successfully',
            'payment_status': payment.status
        })
    
    messages.success(request, f'Payment simulated successfully! Receipt: {payment.mpesa_receipt_number}')
    
    if payment.payment_type == 'deposit':
        return redirect('payment:deposit_success', payment_id=payment_id)
    else:
        return redirect('payment:withdraw_success', payment_id=payment_id)