from django import forms
from .models import VerificationRequest, OTPVerification

class EmailVerificationForm(forms.Form):
    """Request email verification."""
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))


class OTPVerificationForm(forms.Form):
    """Verify OTP code."""
    code = forms.CharField(max_length=6, min_length=6, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter 6-digit code',
        'maxlength': '6',
        'pattern': '[0-9]{6}'
    }))


class IDVerificationForm(forms.ModelForm):
    """ID verification with document upload."""
    
    class Meta:
        model = VerificationRequest
        fields = ['id_number', 'front_id', 'back_id']
        widgets = {
            'id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your National ID number'
            }),
            'front_id': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'back_id': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'id_number': 'National ID Number',
            'front_id': 'Front of ID',
            'back_id': 'Back of ID',
        }
    
    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        if len(id_number) < 6 or len(id_number) > 10:
            raise forms.ValidationError('Please enter a valid Kenyan ID number.')
        return id_number


class SelfieVerificationForm(forms.ModelForm):
    """Selfie verification."""
    
    class Meta:
        model = VerificationRequest
        fields = ['selfie']
        widgets = {
            'selfie': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }


class AddressVerificationForm(forms.ModelForm):
    """Address verification."""
    
    class Meta:
        model = VerificationRequest
        fields = ['physical_address']
        widgets = {
            'physical_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your full physical address'
            }),
        }


class BusinessVerificationForm(forms.ModelForm):
    """Business verification."""
    
    class Meta:
        model = VerificationRequest
        fields = ['business_name', 'business_reg_number', 'kra_pin', 'business_document']
        widgets = {
            'business_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Registered business name'
            }),
            'business_reg_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Business registration number'
            }),
            'kra_pin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'KRA PIN number'
            }),
            'business_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
        }