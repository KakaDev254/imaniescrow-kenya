from django.contrib import admin
from .models import Transaction, TransactionMessage, TransactionMilestone

class TransactionMessageInline(admin.TabularInline):
    model = TransactionMessage
    extra = 0
    readonly_fields = ['created_at']

class TransactionMilestoneInline(admin.TabularInline):
    model = TransactionMilestone
    extra = 0
    readonly_fields = ['created_at']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_id', 'title', 'buyer', 'seller', 'amount',
        'status', 'created_at'
    ]
    list_filter = ['status', 'transaction_type', 'created_at']
    search_fields = ['transaction_id', 'title', 'buyer__email', 'seller__email']
    readonly_fields = ['transaction_id', 'created_at', 'updated_at']
    inlines = [TransactionMessageInline, TransactionMilestoneInline]
    
    fieldsets = (
        ('Transaction Info', {
            'fields': ('transaction_id', 'title', 'description', 'transaction_type')
        }),
        ('Parties', {
            'fields': ('buyer', 'seller')
        }),
        ('Financial Details', {
            'fields': ('amount', 'escrow_fee', 'total_amount')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_reference', 'payment_date')
        }),
        ('Status', {
            'fields': ('status', 'is_disputed')
        }),
        ('Timeline', {
            'fields': ('inspection_period_days', 'delivery_deadline', 'inspection_deadline')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at', 'cancelled_at')
        }),
    )

@admin.register(TransactionMessage)
class TransactionMessageAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'sender', 'created_at']
    list_filter = ['created_at']
    search_fields = ['transaction__transaction_id', 'sender__email']

@admin.register(TransactionMilestone)
class TransactionMilestoneAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'milestone_type', 'created_at']
    list_filter = ['milestone_type', 'created_at']
    search_fields = ['transaction__transaction_id']