from django.urls import path
from . import views

app_name = 'banking'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('deposit/', views.deposit_money, name='deposit_money'),
    path('transfer/', views.transfer_money, name='transfer_money'),
    path('transactions/', views.transaction_history, name='transaction_history'),
    path('create/', views.create_account, name='create_account'), 
    path('account/<int:id>/', views.account_detail, name='account_detail'), 
    path('accounts/<uuid:id>/', views.account_detail, name='account_detail'),
    path('transaction/<uuid:id>/', views.transaction_detail, name='transaction_detail'),
    path('admin/credit/', views.admin_credit_account, name='admin_credit_account'),
    path('manager/dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/approve_account/<uuid:account_id>/', views.approve_account, name='approve_account'),
    path('manager/deny_account/<uuid:account_id>/', views.deny_account, name='deny_account'),
    path('loan/request/', views.loan_request_view, name='loan_request'),
    path('account/<int:id>/', views.account_detail, name='account_detail'),
    path('loan/change/<int:loan_id>/', views.loan_change_view, name='loan_change'),
    path('loan/history/', views.loan_history_view, name='loan_history'),
]
