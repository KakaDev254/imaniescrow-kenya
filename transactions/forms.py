from django import forms
from .models import Transaction, TransactionMessage

class TransactionForm(forms.ModelForm):
    """Form for creating a new escrow transaction."""
    
    class Meta:
        model = Transaction
        fields = [
            'title', 'description', 'transaction_type', 'amount',
            'seller', 'inspection_period_days'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Purchase of iPhone 14'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the item/service in detail...'
            }),
            'transaction_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount in KES',
                'min': '100'
            }),
            'seller': forms.Select(attrs={
                'class': 'form-control'
            }),
            'inspection_period_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '30',
                'value': '3'
            }),
        }
        labels = {
            'title': 'Transaction Title',
            'description': 'Description',
            'transaction_type': 'Type of Transaction',
            'amount': 'Amount (KES)',
            'seller': 'Seller (Email)',
            'inspection_period_days': 'Inspection Period (Days)',
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount < 100:
            raise forms.ValidationError('Minimum transaction amount is KES 100.')
        if amount > 10000000:
            raise forms.ValidationError('Maximum transaction amount is KES 10,000,000.')
        return amount


class TransactionMessageForm(forms.ModelForm):
    """Form for sending messages in a transaction."""
    
    class Meta:
        model = TransactionMessage
        fields = ['message', 'attachment']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Type your message here...'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }


class ConfirmDeliveryForm(forms.Form):
    """Form for confirming delivery."""
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I confirm that I have delivered the item/service as described.'
    )
    delivery_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any delivery notes or tracking information...'
        })
    )


class ConfirmReceiptForm(forms.Form):
    """Form for confirming receipt of goods/services."""
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I confirm that I have received the item/service.'
    )
    satisfied = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I am satisfied and agree to release funds to the seller.'
    )


class DisputeForm(forms.Form):
    """Form for raising a dispute."""
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Explain the reason for the dispute in detail...'
        }),
        label='Dispute Reason'
    )
    evidence = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label='Upload Evidence (optional)',
        help_text='Upload screenshots, photos, or documents to support your claim.'
    )