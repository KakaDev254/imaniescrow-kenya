import random
import uuid
from django.utils import timezone
from django.conf import settings

class MpesaService:
    """M-PESA Service - Works in test mode without real API credentials."""
    
    def __init__(self):
        self._config = None
        self._test_mode = None
    
    @property
    def config(self):
        """Lazy load config to avoid import errors."""
        if self._config is None:
            from .models import MpesaConfig
            self._config = MpesaConfig.objects.filter(is_active=True).first()
        return self._config
    
    @property
    def test_mode(self):
        """Check if test mode is active."""
        if self._test_mode is None:
            config = self.config
            self._test_mode = config.test_mode if config else True
        return self._test_mode
    
    def initiate_stk_push(self, phone_number, amount, payment_type, user, transaction=None, description="Payment"):
        """
        Initiate M-PESA STK Push payment.
        In test mode: Simulates the process without real API calls.
        In production: Uses real Safaricom Daraja API.
        """
        from .models import MpesaPayment
        
        # Format phone number
        if phone_number.startswith('0'):
            phone_number = '+254' + phone_number[1:]
        elif not phone_number.startswith('+254'):
            phone_number = '+254' + phone_number
        
        # Create payment record
        payment = MpesaPayment.objects.create(
            user=user,
            transaction=transaction,
            payment_type=payment_type,
            phone_number=phone_number,
            amount=amount,
            status='processing',
            is_test=self.test_mode
        )
        
        if self.test_mode:
            # Simulate STK Push
            merchant_request_id = f"TEST{uuid.uuid4().hex[:8].upper()}"
            checkout_request_id = f"TEST{uuid.uuid4().hex[:8].upper()}"
            
            payment.merchant_request_id = merchant_request_id
            payment.checkout_request_id = checkout_request_id
            payment.status = 'processing'
            payment.save()
            
            return {
                'success': True,
                'message': f'STK Push sent to {phone_number} (TEST MODE)',
                'payment_id': str(payment.id),
                'payment_reference': payment.payment_reference,
                'merchant_request_id': merchant_request_id,
                'checkout_request_id': checkout_request_id,
                'is_test': True
            }
        else:
            # Production mode placeholder
            return {
                'success': False,
                'message': 'Production mode requires real M-PESA API credentials',
                'payment_id': str(payment.id),
                'payment_reference': payment.payment_reference,
            }
    
    def confirm_payment(self, payment_id):
        """
        Confirm/query payment status.
        In test mode: Auto-completes the payment.
        In production: Queries M-PESA API.
        """
        from .models import MpesaPayment
        
        try:
            payment = MpesaPayment.objects.get(id=payment_id)
        except MpesaPayment.DoesNotExist:
            return {'success': False, 'message': 'Payment not found'}
        
        if self.test_mode:
            # Simulate successful payment
            payment.status = 'completed'
            payment.result_code = '0'
            payment.result_description = 'Success. Transaction completed (TEST MODE)'
            payment.mpesa_receipt_number = f"TEST{random.randint(1000000, 9999999)}"
            payment.completed_at = timezone.now()
            payment.save()
            
            return {
                'success': True,
                'message': 'Payment confirmed successfully (TEST MODE)',
                'payment_reference': payment.payment_reference,
                'mpesa_receipt_number': payment.mpesa_receipt_number,
                'amount': str(payment.amount),
                'is_test': True
            }
        else:
            return {
                'success': False,
                'message': 'Production mode - real API call needed',
            }
    
    def process_deposit(self, payment):
        """Process deposit to escrow account."""
        from .models import EscrowBalance
        
        # Get or create escrow balance
        escrow_balance, created = EscrowBalance.objects.get_or_create(user=payment.user)
        
        # Update balances
        escrow_balance.available_balance += payment.amount
        escrow_balance.total_deposited += payment.amount
        escrow_balance.save()
        
        # Update user account balance
        payment.user.account_balance += payment.amount
        payment.user.save()
        
        return {
            'success': True,
            'message': f'KES {payment.amount} deposited to escrow',
            'new_balance': str(escrow_balance.available_balance)
        }
    
    def process_withdrawal(self, payment):
        """Process withdrawal from escrow account."""
        from .models import EscrowBalance
        
        try:
            escrow_balance = EscrowBalance.objects.get(user=payment.user)
        except EscrowBalance.DoesNotExist:
            return {'success': False, 'message': 'No escrow balance found'}
        
        if escrow_balance.available_balance >= payment.amount:
            escrow_balance.available_balance -= payment.amount
            escrow_balance.total_withdrawn += payment.amount
            escrow_balance.save()
            
            payment.user.account_balance -= payment.amount
            payment.user.save()
            
            return {
                'success': True,
                'message': f'KES {payment.amount} withdrawn successfully',
                'new_balance': str(escrow_balance.available_balance)
            }
        else:
            return {
                'success': False,
                'message': 'Insufficient balance'
            }


class MpesaTestHelper:
    """Helper class for testing M-PESA flows."""
    
    @staticmethod
    def simulate_stk_push(phone_number, amount):
        """Simulate receiving STK push on phone."""
        return {
            'message': f'SIMULATION: STK Push sent to {phone_number} for KES {amount}',
            'prompt': 'Enter M-PESA PIN to complete payment',
            'test_pin': '0000'
        }
    
    @staticmethod
    def simulate_payment_confirmation():
        """Simulate payment confirmation from M-PESA."""
        return {
            'success': True,
            'message': 'SIMULATION: Payment received successfully',
            'receipt': f'TEST{random.randint(1000000, 9999999)}',
            'date': timezone.now().isoformat()
        }
    
    @staticmethod
    def get_test_phone_numbers():
        """Return valid test phone numbers."""
        return [
            '+254712345678',
            '+254723456789',
            '+254734567890',
            '+254745678901',
        ]