from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from .forms import CustomUserCreationForm, CustomUserChangeForm, UserLoginForm, PasswordResetRequestForm
from .models import CustomUser, UserVerification

def register_view(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create email verification token
            verification = UserVerification.objects.create(
                user=user,
                verification_type='email',
                expires_at=timezone.now() + timedelta(hours=24)
            )
            
            # Send verification email (in production)
            # send_verification_email(user.email, verification.token)
            
            messages.success(
                request, 
                'Account created successfully! Please verify your email address.'
            )
            
            # Log the user in
            login(request, user)
            return redirect('dashboard:home')
    else:
        form = CustomUserCreationForm()
    
    context = {'form': form}
    return render(request, 'users/register.html', context)

def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                
                if not remember_me:
                    # Session expires when browser closes
                    request.session.set_expiry(0)
                
                messages.success(request, f'Welcome back, {user.first_name}!')
                
                # Redirect to next page if exists
                next_page = request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect('dashboard:home')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserLoginForm()
    
    context = {'form': form}
    return render(request, 'users/login.html', context)

@login_required
def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')

@login_required
def profile_view(request):
    """Display user profile."""
    context = {'user': request.user}
    return render(request, 'users/profile.html', context)

@login_required
def edit_profile_view(request):
    """Edit user profile."""
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    context = {'form': form}
    return render(request, 'users/edit_profile.html', context)

def password_reset_request_view(request):
    """Handle password reset request."""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                
                # Create reset token
                verification = UserVerification.objects.create(
                    user=user,
                    verification_type='password_reset',
                    expires_at=timezone.now() + timedelta(hours=1)
                )
                
                # Send password reset email (in production)
                # send_password_reset_email(user.email, verification.token)
                
                messages.success(
                    request, 
                    'Password reset link has been sent to your email.'
                )
                return redirect('users:login')
            except CustomUser.DoesNotExist:
                messages.error(request, 'No account found with this email address.')
    else:
        form = PasswordResetRequestForm()
    
    context = {'form': form}
    return render(request, 'users/password_reset.html', context)