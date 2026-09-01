from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
import uuid

class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with email as the unique identifier."""
    
    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Custom User Model with email as the unique identifier."""
    
    username = None
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    
    # Phone number validation for Kenyan numbers
    phone_regex = RegexValidator(
        regex=r'^\+?254?\d{9,12}$',
        message="Phone number must be entered in the format: '+254XXXXXXXXX' or '254XXXXXXXXX'. Up to 12 digits allowed."
    )
    
    # Additional fields
    phone_number = models.CharField(
        validators=[phone_regex], 
        max_length=13, 
        unique=True,
        null=True, 
        blank=True,
        help_text="Kenyan phone number (e.g., +254712345678)"
    )
    national_id = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True,
        verbose_name="National ID Number"
    )
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Profile information
    # Cloudinary will handle image storage automatically when configured
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        null=True, 
        blank=True,
        help_text="Upload a profile picture (stored on Cloudinary)"
    )
    bio = models.TextField(max_length=500, blank=True)
    
    # Address fields
    city = models.CharField(max_length=100, blank=True)
    county = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    
    # Verification status
    is_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    
    # M-PESA details
    mpesa_name = models.CharField(max_length=100, blank=True)
    has_mpesa = models.BooleanField(default=True)
    
    # Account balance
    account_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return the full name of the user."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email.split('@')[0]
    
    def get_verification_status(self):
        """Return overall verification status."""
        return all([
            self.is_verified,
            self.is_phone_verified,
            self.is_email_verified
        ])
    
    def get_profile_picture_url(self):
        """Return profile picture URL or a default avatar."""
        if self.profile_picture:
            return self.profile_picture.url
        return f"https://ui-avatars.com/api/?name={self.first_name}+{self.last_name}&background=006600&color=fff"


class UserVerification(models.Model):
    """Store verification tokens and status."""
    
    VERIFICATION_TYPES = [
        ('email', 'Email Verification'),
        ('phone', 'Phone Verification'),
        ('id', 'ID Verification'),
        ('password_reset', 'Password Reset'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='verifications')
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPES)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.verification_type}"
    
    def is_valid(self):
        """Check if token is still valid."""
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()