from django.urls import path
from . import views

app_name = 'verification'

urlpatterns = [
    path('', views.verification_center, name='center'),
    path('send-email-otp/', views.send_email_otp, name='send_email_otp'),
    path('send-phone-otp/', views.send_phone_otp, name='send_phone_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('verify-id/', views.verify_id, name='verify_id'),
    path('verify-selfie/', views.verify_selfie, name='verify_selfie'),
    path('verify-address/', views.verify_address, name='verify_address'),
    path('verify-business/', views.verify_business, name='verify_business'),
]