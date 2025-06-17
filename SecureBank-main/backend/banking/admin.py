from django.contrib import admin
from .models import Account, Transaction

@admin.action(description="Freeze selected accounts")
def freeze_accounts(modeladmin, request, queryset):
    queryset.update(status='FROZEN')

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'account_type', 'account_number', 'balance', 'is_active', 'status', 'created_at']
    search_fields = ['user__username', 'account_number']
    list_filter = ['account_type', 'is_active', 'status', 'created_at']
    actions = [freeze_accounts]

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_type', 'from_account', 'to_account', 'amount', 'status', 'reference_number', 'created_at']
    search_fields = ['reference_number', 'from_account__account_number']
    list_filter = ['transaction_type', 'status', 'created_at']