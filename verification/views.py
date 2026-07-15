from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .models import VerificationRequest, OTPVerification
from .forms import (
    OTPVerificationForm, IDVerificationForm,
    SelfieVerificationForm, AddressVerificationForm,
    BusinessVerificationForm
)
import random

@login_required
def verification_center(request):
    """Main verification center showing all verification statuses."""
    
    verifications = VerificationRequest.objects.filter(user=request.user)
    
    # Check what's verified
    context = {
        'is_email_verified': request.user.is_email_verified,
        'is_phone_verified': request.user.is_phone_verified,
        'is_id_verified': verifications.filter(verification_type='id', status='approved').exists(),
        'is_selfie_verified': verifications.filter(verification_type='selfie', status='approved').exists(),
        'is_address_verified': verifications.filter(verification_type='address', status='approved').exists(),
        'is_business_verified': verifications.filter(verification_type='business', status='approved').exists(),
        'pending_verifications': verifications.filter(status__in=['pending', 'in_review']),
        'completed_verifications': verifications.filter(status='approved'),
        'rejected_verifications': verifications.filter(status='rejected'),
    }
    return render(request, 'verification/center.html', context)


@login_required
def send_email_otp(request):
    """Send OTP to user's email for verification."""
    
    if request.user.is_email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('verification:center')
    
    # Generate OTP
    code = str(random.randint(100000, 999999))
    
    # Create OTP record
    OTPVerification.objects.create(
        user=request.user,
        verification_type='email',
        code=code
    )
    
    # In production: Send email with OTP
    # send_email_otp(request.user.email, code)
    
    # For testing, show OTP
    messages.success(request, f'OTP sent to your email. (Test OTP: {code})')
    request.session['verification_type'] = 'email'
    request.session['show_test_otp'] = code
    
    return redirect('verification:verify_otp')


@login_required
def send_phone_otp(request):
    """Send OTP to user's phone via SMS."""
    
    if request.user.is_phone_verified:
        messages.info(request, 'Your phone is already verified.')
        return redirect('verification:center')
    
    if not request.user.phone_number:
        messages.error(request, 'Please add a phone number to your profile first.')
        return redirect('users:edit_profile')
    
    # Generate OTP
    code = str(random.randint(100000, 999999))
    
    # Create OTP record
    OTPVerification.objects.create(
        user=request.user,
        verification_type='phone',
        code=code
    )
    
    # In production: Send SMS via Africa's Talking
    # send_sms_otp(request.user.phone_number, code)
    
    messages.success(request, f'OTP sent to your phone. (Test OTP: {code})')
    request.session['verification_type'] = 'phone'
    request.session['show_test_otp'] = code
    
    return redirect('verification:verify_otp')


@login_required
def verify_otp(request):
    """Verify OTP code."""
    
    verification_type = request.session.get('verification_type')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            
            # Find valid OTP
            otp = OTPVerification.objects.filter(
                user=request.user,
                verification_type=verification_type,
                is_used=False
            ).order_by('-created_at').first()
            
            if otp and otp.is_valid() and otp.code == code:
                # Mark OTP as used
                otp.is_used = True
                otp.save()
                
                # Create verification request
                verification = VerificationRequest.objects.create(
                    user=request.user,
                    verification_type=verification_type,
                    status='approved'
                )
                verification.approve()
                
                # Update user
                if verification_type == 'email':
                    request.user.is_email_verified = True
                elif verification_type == 'phone':
                    request.user.is_phone_verified = True
                request.user.save()
                
                messages.success(request, f'{verification_type.title()} verified successfully!')
                
                # Clear session
                request.session.pop('verification_type', None)
                request.session.pop('show_test_otp', None)
                
                return redirect('verification:center')
            else:
                messages.error(request, 'Invalid or expired OTP. Please try again.')
    else:
        form = OTPVerificationForm()
    
    context = {
        'form': form,
        'verification_type': verification_type,
        'test_otp': request.session.get('show_test_otp'),
    }
    return render(request, 'verification/verify_otp.html', context)


@login_required
def verify_id(request):
    """ID verification with document upload."""
    
    # Check if already verified or pending
    existing = VerificationRequest.objects.filter(
        user=request.user,
        verification_type='id',
        status__in=['pending', 'in_review', 'approved']
    ).exists()
    
    if existing:
        messages.info(request, 'ID verification already submitted or approved.')
        return redirect('verification:center')
    
    if request.method == 'POST':
        form = IDVerificationForm(request.POST, request.FILES)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.user = request.user
            verification.verification_type = 'id'
            verification.status = 'in_review'  # Auto-approve for test mode
            verification.save()
            
            # In test mode: Auto-approve after 2 seconds
            verification.approve()
            messages.success(request, 'ID verified successfully! (Auto-approved in test mode)')
            return redirect('verification:center')
    else:
        form = IDVerificationForm()
    
    context = {'form': form, 'verification_type': 'ID'}
    return render(request, 'verification/upload_document.html', context)


@login_required
def verify_selfie(request):
    """Selfie verification."""
    
    existing = VerificationRequest.objects.filter(
        user=request.user,
        verification_type='selfie',
        status__in=['pending', 'in_review', 'approved']
    ).exists()
    
    if existing:
        messages.info(request, 'Selfie verification already submitted.')
        return redirect('verification:center')
    
    if request.method == 'POST':
        form = SelfieVerificationForm(request.POST, request.FILES)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.user = request.user
            verification.verification_type = 'selfie'
            verification.status = 'in_review'
            verification.save()
            
            # Auto-approve in test mode
            verification.approve()
            messages.success(request, 'Selfie verified successfully! (Auto-approved)')
            return redirect('verification:center')
    else:
        form = SelfieVerificationForm()
    
    context = {'form': form, 'verification_type': 'Selfie'}
    return render(request, 'verification/upload_document.html', context)


@login_required
def verify_address(request):
    """Address verification."""
    
    existing = VerificationRequest.objects.filter(
        user=request.user,
        verification_type='address',
        status__in=['pending', 'in_review', 'approved']
    ).exists()
    
    if existing:
        messages.info(request, 'Address verification already submitted.')
        return redirect('verification:center')
    
    if request.method == 'POST':
        form = AddressVerificationForm(request.POST)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.user = request.user
            verification.verification_type = 'address'
            verification.status = 'in_review'
            verification.save()
            
            verification.approve()
            messages.success(request, 'Address verified successfully!')
            return redirect('verification:center')
    else:
        form = AddressVerificationForm()
    
    context = {'form': form, 'verification_type': 'Address'}
    return render(request, 'verification/verify_address.html', context)


@login_required
def verify_business(request):
    """Business verification."""
    
    existing = VerificationRequest.objects.filter(
        user=request.user,
        verification_type='business',
        status__in=['pending', 'in_review', 'approved']
    ).exists()
    
    if existing:
        messages.info(request, 'Business verification already submitted.')
        return redirect('verification:center')
    
    if request.method == 'POST':
        form = BusinessVerificationForm(request.POST, request.FILES)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.user = request.user
            verification.verification_type = 'business'
            verification.status = 'in_review'
            verification.save()
            
            verification.approve()
            messages.success(request, 'Business verified successfully!')
            return redirect('verification:center')
    else:
        form = BusinessVerificationForm()
    
    context = {'form': form, 'verification_type': 'Business'}
    return render(request, 'verification/verify_business.html', context)