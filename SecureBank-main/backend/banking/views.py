from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from .models import Loan
from .models import Account, Transaction
from .forms import CreateAccountForm, DepositForm, TransferForm
import uuid
from decimal import Decimal
from django.conf import settings
from .forms import LoanRequestForm
from django.urls import reverse


@staff_member_required
def manager_dashboard(request):
    pending_accounts = Account.objects.filter(status='PENDING')
    customers = Account.objects.all()
    try:
        from .models import Loan
        pending_loans = Loan.objects.filter(status='PENDING')
    except ImportError:
        pending_loans = []
    transactions = Transaction.objects.all()[:50]
    return render(request, 'banking/manager_dashboard.html', {
        'pending_accounts': pending_accounts,
        'customers': customers,
        'pending_loans': pending_loans,
        'transactions': transactions,
    })

@staff_member_required
def approve_account(request, account_id):
    account = get_object_or_404(Account, id=account_id, status='PENDING')
    account.status = 'APPROVED'
    account.save()
    messages.success(request, f"Account {account.account_number} approved.")
    return redirect('manager_dashboard')

@staff_member_required
def deny_account(request, account_id):
    account = get_object_or_404(Account, id=account_id, status='PENDING')
    account.status = 'DENIED'
    account.save()
    messages.success(request, f"Account {account.account_number} denied.")
    return redirect('manager_dashboard')

@login_required
def dashboard(request):
    accounts = Account.objects.filter(user=request.user)
    recent_transactions = Transaction.objects.filter(
        Q(from_account__in=accounts) | Q(to_account__in=accounts)
    ).order_by('-created_at')[:5]

    return render(request, 'banking/dashboard.html', {
        'accounts': accounts,
        'recent_transactions': recent_transactions
    })

@login_required
def account_detail(request, id):
    account = get_object_or_404(Account, id=id, user=request.user)
    transactions = Transaction.objects.filter(
        Q(from_account=account) | Q(to_account=account)
    ).order_by('-created_at')

    return render(request, 'banking/account_detail.html', {
        'account': account,
        'transactions': transactions
    })

@login_required
@require_http_methods(["GET", "POST"])
def deposit_money(request):
    user_account = Account.objects.filter(user=request.user).first()
    # Prevent deposit if account is not approved or is frozen
    if user_account and (user_account.status != 'APPROVED' or user_account.status == 'FROZEN'):
        messages.error(request, "Your account is not approved or is frozen. You cannot deposit.")
        return redirect('banking:dashboard')

    if request.method == "POST":
        form = DepositForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            amount = form.cleaned_data['amount']

            # Prevent depositing to own account
            if user_account and user_account.phone_number == phone_number:
                messages.error(request, "You cannot deposit money into your own account.")
                return redirect('banking:deposit_money')

            account = Account.objects.filter(phone_number=phone_number).first()

            if account:
                account.balance += amount
                account.save()

                Transaction.objects.create(
                    from_account=account,
                    to_account=account,
                    transaction_type='DEPOSIT',
                    amount=amount,
                    status='COMPLETED',
                    reference_number=str(uuid.uuid4()),
                    description=f"Deposit from {phone_number}"
                )

                messages.success(request, f"Successfully deposited {amount} FCFA to {phone_number}.")
                return redirect('banking:dashboard')
            else:
                messages.error(request, f"No account found with phone number: {phone_number}.")
    else:
        form = DepositForm()

    return render(request, 'banking/deposit_money.html', {'form': form})

@staff_member_required
@require_http_methods(["GET", "POST"])
def admin_credit_account(request):
    if request.method == "POST":
        phone_number = request.POST.get("phone_number")
        try:
            amount = Decimal(request.POST.get("amount", 0))
        except (TypeError, ValueError):
            amount = Decimal("0")
        if amount <= 0:
            messages.error(request, "Amount must be positive.")
        else:
            account = Account.objects.filter(phone_number=phone_number).first()
            if account:
                account.balance += amount
                account.save()
                Transaction.objects.create(
                    from_account=account,
                    to_account=account,
                    transaction_type='ADMIN_CREDIT',
                    amount=amount,
                    status='COMPLETED',
                    reference_number=str(uuid.uuid4()),
                    description=f"Admin credited {amount} FCFA"
                )
                messages.success(request, f"Credited {amount} FCFA to {phone_number}.")
            else:
                messages.error(request, "Account not found.")
    return render(request, "banking/admin_credit_account.html")

@login_required
@require_http_methods(["GET", "POST"])
def transfer_money(request):
    sender_account = Account.objects.filter(user=request.user).first()

    # Prevent transfer if account is not approved or is frozen
    if sender_account and (sender_account.status != 'APPROVED' or sender_account.status == 'FROZEN'):
        messages.error(request, "Your account is not approved or is frozen. You cannot transfer money.")
        return redirect('banking:dashboard')

    if not sender_account:
        messages.error(request, "You don't have an account to transfer from. Please create one first.")
        return redirect('banking:create_account')

    if request.method == "POST":
        form = TransferForm(request.POST)
        if form.is_valid():
            recipient_phone = form.cleaned_data['phone_number']
            amount = form.cleaned_data['amount']
            password = form.cleaned_data['password']

            user = authenticate(username=request.user.username, password=password)

            if not user:
                messages.error(request, "Authentication failed. Please check your password.")
            elif recipient_phone == sender_account.phone_number:
                messages.error(request, "You cannot transfer to your own account.")
            else:
                recipient_account = Account.objects.filter(phone_number=recipient_phone).first()

                if not recipient_account:
                    messages.error(request, f"No account found with phone number: {recipient_phone}.")
                elif sender_account.balance < amount:
                    messages.error(request, "Insufficient balance for this transfer.")
                else:
                    sender_account.balance -= amount
                    recipient_account.balance += amount
                    sender_account.save()
                    recipient_account.save()

                    reference_number = str(uuid.uuid4())
                    Transaction.objects.create(
                        from_account=sender_account,
                        to_account=recipient_account,
                        transaction_type='TRANSFER',
                        amount=amount,
                        status='COMPLETED',
                        reference_number=reference_number,
                        description=f"Transfer to {recipient_phone}"
                    )
                    send_mail(
                        subject="You've received a transfer",
                        message=f"You have received {amount} FCFA from {request.user.username}.",
                        from_email="noreply@securebank.com",
                        recipient_list=[recipient_account.user.email],
                    )

                    # Show confirmation page instead of redirecting to dashboard
                    return render(request, 'banking/transfer_confirmation.html', {
                        'recipient': recipient_account,
                        'amount': amount,
                        'reference': reference_number,
                    })
    else:
        form = TransferForm()

    return render(request, 'banking/transfer_money.html', {'form': form})

@login_required
def transaction_detail(request, id):
    transaction = get_object_or_404(Transaction, id=id)
    user_accounts = Account.objects.filter(user=request.user)
    # Optional: Only allow users involved in the transaction to view it
    if transaction.from_account not in user_accounts and transaction.to_account not in user_accounts:
        messages.error(request, "You do not have permission to view this transaction.")
        return redirect('banking:dashboard')
    return render(request, 'banking/transaction_detail.html', {'transaction': transaction})

@login_required
def transaction_history(request):
    accounts = Account.objects.filter(user=request.user)
    transactions = Transaction.objects.filter(
        Q(from_account__in=accounts) | Q(to_account__in=accounts)
    ).order_by('-created_at')

    return render(request, 'banking/transaction_history.html', {
        'transactions': transactions
    })

@login_required
@require_http_methods(["GET", "POST"])
def create_account(request):
    if request.method == "POST":
        form = CreateAccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            if not account.account_number:
                account.account_number = str(uuid.uuid4().int)[:10]
            account.save()
            messages.success(request, "Account successfully created.")
            return redirect('banking:dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CreateAccountForm()

    return render(request, 'banking/create_account.html', {
        'form': form,
        'account_types': Account.ACCOUNT_TYPES
    })
    
@csrf_protect
@login_required
def loan_request_view(request):
    if request.method == 'POST':
        form = LoanRequestForm(request.POST, user=request.user)
        if form.is_valid():
            loan = form.save(commit=False)
            # Get the user's account (adjust if user can have multiple accounts)
            account = get_object_or_404(Account, user=request.user)
            loan.account = account
            loan.user = request.user
            loan.save()
            return redirect('banking:loan_history')
    else:
        form = LoanRequestForm(user=request.user)
    return render(request, 'banking/loan_request.html', {'form': form})

def loan_change_view(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    # Add your logic for changing the loan here
    return render(request, 'banking/loan_change.html', {'loan': loan})

    
@login_required
def loan_history_view(request):
    loans = Loan.objects.filter(account__user=request.user).order_by('-requested_at')
    return render(request, 'banking/loan_history.html', {'loans': loans})