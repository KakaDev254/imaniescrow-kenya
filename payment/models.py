from django.db import models
from django.conf import settings
from transactions.models import Transaction
import uuid

class MpesaConfig(models.Model):
    """M-PESA API Configuration - Add real credentials here later."""
    
    ENVIRONMENT_CHOICES = [
        ('sandbox', 'Sandbox (Testing)'),
        ('production', 'Production (Live)'),
    ]
    
    name = models.CharField(max_length=100, default='M-PESA Configuration')
    environment = models.CharField(max_length=20, choices=ENVIRONMENT_CHOICES, default='sandbox')
    consumer_key = models.CharField(max_length=100, blank=True, help_text='From Safaricom Developer Portal')
    consumer_secret = models.CharField(max_length=100, blank=True)
    passkey = models.CharField(max_length=100, blank=True)
    shortcode = models.CharField(max_length=10, default='174379')
    test_mode = models.BooleanField(default=True, help_text='Enable test mode without real API calls')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.environment}"
    
    class Meta:
        verbose_name = 'M-PESA Configuration'
        verbose_name_plural = 'M-PESA Configurations'


class MpesaPayment(models.Model):
    """M-PESA Payment Records."""
    
    PAYMENT_TYPE_CHOICES = [
        ('deposit', 'Deposit to Escrow'),
        ('withdrawal', 'Withdrawal from Escrow'),
        ('refund', 'Refund'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_reference = models.CharField(max_length=50, unique=True)
    
    # User and transaction
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mpesa_payments')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='mpesa_payments')
    
    # Payment details
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    phone_number = models.CharField(max_length=13)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # M-PESA response fields
    merchant_request_id = models.CharField(max_length=50, blank=True)
    checkout_request_id = models.CharField(max_length=50, blank=True)
    result_code = models.CharField(max_length=10, blank=True)
    result_description = models.TextField(blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_test = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.payment_reference} - {self.payment_type} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'M-PESA Payment'
        verbose_name_plural = 'M-PESA Payments'
    
    def save(self, *args, **kwargs):
        if not self.payment_reference:
            self.payment_reference = f"MPESA{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)


class EscrowBalance(models.Model):
    """Track user escrow balances."""
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='escrow_balance')
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    held_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_deposited = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_withdrawn = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - Balance: KES {self.available_balance}"
    
    class Meta:
        verbose_name = 'Escrow Balance'
        verbose_name_plural = 'Escrow Balances'