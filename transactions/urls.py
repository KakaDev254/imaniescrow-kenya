from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.transaction_list, name='list'),
    path('create/', views.create_transaction, name='create'),
    path('<str:transaction_id>/', views.transaction_detail, name='detail'),
    path('<str:transaction_id>/confirm-payment/', views.confirm_payment, name='confirm_payment'),
    path('<str:transaction_id>/confirm-delivery/', views.confirm_delivery, name='confirm_delivery'),
    path('<str:transaction_id>/confirm-receipt/', views.confirm_receipt, name='confirm_receipt'),
    path('<str:transaction_id>/dispute/', views.raise_dispute, name='dispute'),
    path('<str:transaction_id>/cancel/', views.cancel_transaction, name='cancel'),
]