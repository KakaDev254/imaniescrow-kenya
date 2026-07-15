from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserVerification

class CustomUserAdmin(UserAdmin):
    """Define admin model for custom User model."""
    
    model = CustomUser
    
    # Fields to display in list view
    list_display = (
        'email', 'first_name', 'last_name', 'phone_number',
        'is_verified', 'is_staff', 'is_active', 'date_joined'
    )
    list_filter = (
        'is_verified', 'is_staff', 'is_active', 'county', 'date_joined'
    )
    
    # Fields for editing
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name', 'last_name', 'phone_number', 'national_id',
                'date_of_birth', 'profile_picture', 'bio'
            )
        }),
        (_('Address'), {
            'fields': ('city', 'county', 'postal_code')
        }),
        (_('Verification'), {
            'fields': (
                'is_verified', 'is_phone_verified', 'is_email_verified'
            )
        }),
        (_('M-PESA Details'), {
            'fields': ('mpesa_name', 'has_mpesa')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # Fields for adding new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'phone_number',
                'password1', 'password2', 'is_staff', 'is_active'
            ),
        }),
    )
    
    search_fields = ('email', 'first_name', 'last_name', 'phone_number', 'national_id')
    ordering = ('email',)
    readonly_fields = ('date_joined', 'last_login')

class UserVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'verification_type', 'is_used', 'created_at', 'expires_at')
    list_filter = ('verification_type', 'is_used')
    search_fields = ('user__email', 'user__phone_number')

# Register models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserVerification, UserVerificationAdmin)