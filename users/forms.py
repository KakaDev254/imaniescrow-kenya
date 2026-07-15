from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import CustomUser
import re

class CustomUserCreationForm(UserCreationForm):
    """Form for user registration."""
    
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    email = forms.EmailField(
        max_length=254, 
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    phone_number = forms.CharField(
        max_length=13, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., +254712345678'
        }),
        help_text='Enter your Kenyan phone number in format: +254XXXXXXXXX'
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    
    # Terms and conditions
    agree_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I agree to the Terms and Conditions'
    )
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2')
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        
        # Remove any spaces or dashes
        phone = re.sub(r'[\s\-]', '', phone)
        
        # Ensure it starts with +254 or 254
        if phone.startswith('0'):
            phone = '+254' + phone[1:]
        elif phone.startswith('7'):
            phone = '+254' + phone
        elif not phone.startswith('+254'):
            phone = '+254' + phone
        
        # Validate length (12-13 characters including +)
        if len(phone) < 12 or len(phone) > 13:
            raise ValidationError('Phone number must be 12-13 digits including country code.')
        
        # Check if phone number already exists
        if CustomUser.objects.filter(phone_number=phone).exists():
            raise ValidationError('This phone number is already registered.')
        
        return phone
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.username = user.email  # Set username to email
        
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """Form for updating user profile."""
    
    class Meta:
        model = CustomUser
        fields = (
            'first_name', 'last_name', 'phone_number', 'national_id',
            'date_of_birth', 'profile_picture', 'bio', 'city', 'county',
            'postal_code', 'mpesa_name'
        )
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class UserLoginForm(forms.Form):
    """Form for user login."""
    
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Remember me'
    )


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset."""
    
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email'
        })
    )