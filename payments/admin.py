from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'payment_method', 'sender_number', 'transaction_id_short', 'status', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('booking__id', 'sender_number', 'transaction_id')
    list_editable = ('status',)
    readonly_fields = ('booking', 'amount', 'payment_method', 'sender_number', 'transaction_id', 'created_at', 'updated_at')
    actions = ['approve_payments', 'reject_payments']

    def transaction_id_short(self, obj):
        return obj.transaction_id[:30] + '...' if len(obj.transaction_id) > 30 else obj.transaction_id
    transaction_id_short.short_description = 'Transaction ID'

    def approve_payments(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} payment(s) approved successfully.')
    approve_payments.short_description = '✅ Approve selected payments'

    def reject_payments(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} payment(s) rejected.')
    reject_payments.short_description = '❌ Reject selected payments'
