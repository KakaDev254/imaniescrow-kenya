from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('deposit/', views.deposit_funds, name='deposit'),
    path('deposit/<uuid:payment_id>/confirm/', views.confirm_deposit, name='confirm_deposit'),
    path('deposit/<uuid:payment_id>/success/', views.deposit_success, name='deposit_success'),
    path('withdraw/', views.withdraw_funds, name='withdraw'),
    path('withdraw/<uuid:payment_id>/success/', views.withdraw_success, name='withdraw_success'),
    path('history/', views.payment_history, name='history'),
    path('simulate-callback/<uuid:payment_id>/', views.simulate_payment_callback, name='simulate_callback'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
]