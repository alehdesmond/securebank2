from django import forms
from .models import Account, Loan
from django.core.exceptions import ValidationError
import re

# ✅ Updated phone number validator
def validate_cameroon_phone(value):
    pattern_with_plus = r'^\+2376[0-9]{8}$'
    pattern_without_plus = r'^6[0-9]{8}$'
    if not re.match(pattern_with_plus, value) and not re.match(pattern_without_plus, value):
        raise forms.ValidationError("Enter a valid Cameroonian phone number starting with +237 or just 6XXXXXXXX.")


class CreateAccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['account_type', 'account_number', 'phone_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account_number'].required = False
        self.fields['phone_number'].validators = [validate_cameroon_phone]


class DepositForm(forms.Form):
    phone_number = forms.CharField(validators=[validate_cameroon_phone])
    amount = forms.DecimalField(min_value=1.0)


class TransferForm(forms.Form):
    phone_number = forms.CharField(validators=[validate_cameroon_phone], label="Recipient Phone Number")
    password = forms.CharField(widget=forms.PasswordInput)
    amount = forms.DecimalField(min_value=100.0, decimal_places=2, label="Transfer Amount")


# ✅ Corrected LoanRequestForm to accept `user` as an optional kwarg
class LoanRequestForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['amount', 'term']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # ✅ Accept user safely
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError("Loan amount must be greater than zero.")
        return amount

    def clean_term(self):
        term = self.cleaned_data.get('term')
        if term <= 0:
            raise ValidationError("Loan term must be greater than zero.")
        return term
