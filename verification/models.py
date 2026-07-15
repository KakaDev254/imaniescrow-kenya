from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid

class VerificationLevel(models.Model):
    """Verification levels and their requirements."""
    
    LEVEL_CHOICES = [
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('business', 'Business'),
    ]
    
    name = models.CharField(max_length=20, choices=LEVEL_CHOICES, unique=True)
    description = models.TextField()
    transaction_limit = models.DecimalField(max_digits=12, decimal_places=2, help_text='Maximum transaction amount')
    daily_limit = models.DecimalField(max_digits=12, decimal_places=2, help_text='Daily transaction limit')
    monthly_limit = models.DecimalField(max_digits=12, decimal_places=2, help_text='Monthly transaction limit')
    requires_email = models.BooleanField(default=True)
    requires_phone = models.BooleanField(default=True)
    requires_id = models.BooleanField(default=False)
    requires_selfie = models.BooleanField(default=False)
    requires_address = models.BooleanField(default=False)
    requires_business_docs = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['transaction_limit']
    
    def __str__(self):
        return f"{self.get_name_display()} - KES {self.transaction_limit}"


class VerificationRequest(models.Model):
    """User verification requests."""
    
    VERIFICATION_TYPE_CHOICES = [
        ('email', 'Email Verification'),
        ('phone', 'Phone Verification'),
        ('id', 'ID Verification'),
        ('selfie', 'Selfie Verification'),
        ('address', 'Address Verification'),
        ('business', 'Business Verification'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verification_requests')
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Documents
    front_id = models.ImageField(upload_to='verification/id_front/', null=True, blank=True)
    back_id = models.ImageField(upload_to='verification/id_back/', null=True, blank=True)
    selfie = models.ImageField(upload_to='verification/selfies/', null=True, blank=True)
    business_document = models.FileField(upload_to='verification/business/', null=True, blank=True)
    
    # Additional info
    id_number = models.CharField(max_length=50, blank=True)
    kra_pin = models.CharField(max_length=20, blank=True, verbose_name='KRA PIN')
    business_name = models.CharField(max_length=200, blank=True)
    business_reg_number = models.CharField(max_length=100, blank=True)
    physical_address = models.TextField(blank=True)
    
    # Admin review
    admin_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_verifications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.verification_type} - {self.status}"
    
    def approve(self, admin_user=None):
        """Approve the verification request."""
        self.status = 'approved'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()
        
        # Update user verification flags
        if self.verification_type == 'email':
            self.user.is_email_verified = True
        elif self.verification_type == 'phone':
            self.user.is_phone_verified = True
        elif self.verification_type in ['id', 'selfie', 'address']:
            self.user.is_verified = True
        
        self.user.save()
        
        # Update verification level
        update_user_verification_level(self.user)
    
    def reject(self, admin_user=None, reason=''):
        """Reject the verification request."""
        self.status = 'rejected'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()


class OTPVerification(models.Model):
    """OTP codes for email and phone verification."""
    
    VERIFICATION_TYPE_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('login', 'Login 2FA'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='otp_codes')
    verification_type = models.CharField(max_length=10, choices=VERIFICATION_TYPE_CHOICES)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.verification_type}"
    
    def is_valid(self):
        """Check if OTP is still valid."""
        return not self.is_used and self.expires_at > timezone.now()
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)


def update_user_verification_level(user):
    """Update user's verification level based on completed verifications."""
    from users.models import CustomUser
    
    # Count completed verifications
    completed = VerificationRequest.objects.filter(
        user=user,
        status='approved'
    ).values_list('verification_type', flat=True)
    
    completed_types = list(completed)
    
    # Determine level
    if 'business' in completed_types and 'id' in completed_types:
        # Check if we need to add verification_level field to CustomUser
        # For now, we'll just update the is_verified flag
        user.is_verified = True
    
    user.save()
    return user