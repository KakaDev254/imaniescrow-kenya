from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid

class Transaction(models.Model):
    """Main escrow transaction model."""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_payment', 'Pending Payment'),
        ('payment_confirmed', 'Payment Confirmed'),
        ('in_progress', 'In Progress'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    TRANSACTION_TYPE_CHOICES = [
        ('goods', 'Goods'),
        ('services', 'Services'),
        ('digital', 'Digital Products'),
        ('property', 'Property'),
        ('other', 'Other'),
    ]
    
    # Transaction identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(max_length=20, unique=True, editable=False)
    
    # Parties involved
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='purchases'
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sales'
    )
    
    # Transaction details
    title = models.CharField(max_length=200)
    description = models.TextField()
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        default='goods'
    )
    
    # Financial details
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(100)]  # Minimum KES 100
    )
    escrow_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Payment details
    payment_method = models.CharField(max_length=20, default='mpesa')
    payment_reference = models.CharField(max_length=50, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Timeline
    inspection_period_days = models.IntegerField(default=3)
    delivery_deadline = models.DateTimeField(null=True, blank=True)
    inspection_deadline = models.DateTimeField(null=True, blank=True)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Delivery confirmation
    seller_delivery_confirmation = models.BooleanField(default=False)
    buyer_receipt_confirmation = models.BooleanField(default=False)
    buyer_satisfaction_confirmation = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Cancellation
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_transactions'
    )
    cancellation_reason = models.TextField(blank=True)
    
    # Dispute
    is_disputed = models.BooleanField(default=False)
    dispute_reason = models.TextField(blank=True)
    dispute_resolution = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
    
    def __str__(self):
        return f"{self.transaction_id} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Generate transaction ID if not set
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        
        # Calculate total amount (amount + escrow fee)
        if not self.total_amount:
            self.total_amount = self.amount + self.escrow_fee
        
        super().save(*args, **kwargs)
    
    def generate_transaction_id(self):
        """Generate a unique transaction ID."""
        import random
        import string
        prefix = 'TRX'
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"{prefix}{random_part}"
    
    def calculate_escrow_fee(self):
        """Calculate escrow fee based on amount."""
        if self.amount <= 10000:
            fee_percentage = 0.02  # 2%
        elif self.amount <= 100000:
            fee_percentage = 0.015  # 1.5%
        elif self.amount <= 1000000:
            fee_percentage = 0.01  # 1%
        else:
            fee_percentage = 0.008  # 0.8%
        
        return round(self.amount * fee_percentage, 2)
    
    def get_status_color(self):
        """Return color based on status."""
        color_map = {
            'draft': '#666666',
            'pending_payment': '#FF6600',
            'payment_confirmed': '#0044CC',
            'in_progress': '#FF6600',
            'delivered': '#006600',
            'completed': '#006600',
            'disputed': '#CC0000',
            'cancelled': '#999999',
            'refunded': '#FF6600',
        }
        return color_map.get(self.status, '#666666')
    
    def get_status_badge(self):
        """Return status with HTML badge."""
        return f'<span style="background-color: {self.get_status_color()}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem;">{self.get_status_display()}</span>'


class TransactionMessage(models.Model):
    """Messages between buyer and seller for a transaction."""
    
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    message = models.TextField()
    attachment = models.FileField(
        upload_to='transaction_attachments/',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Transaction Message'
        verbose_name_plural = 'Transaction Messages'
    
    def __str__(self):
        return f"Message from {self.sender.email} on {self.transaction.transaction_id}"


class TransactionMilestone(models.Model):
    """Track transaction milestones and status changes."""
    
    MILESTONE_CHOICES = [
        ('created', 'Transaction Created'),
        ('payment_initiated', 'Payment Initiated'),
        ('payment_received', 'Payment Received'),
        ('delivery_started', 'Delivery Started'),
        ('delivery_confirmed', 'Delivery Confirmed'),
        ('inspection_started', 'Inspection Period Started'),
        ('buyer_accepted', 'Buyer Accepted'),
        ('funds_released', 'Funds Released to Seller'),
        ('completed', 'Transaction Completed'),
        ('dispute_raised', 'Dispute Raised'),
        ('cancelled', 'Transaction Cancelled'),
        ('refunded', 'Payment Refunded'),
    ]
    
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='milestones'
    )
    milestone_type = models.CharField(max_length=30, choices=MILESTONE_CHOICES)
    description = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transaction Milestone'
        verbose_name_plural = 'Transaction Milestones'
    
    def __str__(self):
        return f"{self.get_milestone_type_display()} - {self.transaction.transaction_id}"