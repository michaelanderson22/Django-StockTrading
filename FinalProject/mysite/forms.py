# forms.py

from django import forms


class AddFundsForm(forms.Form):
    amount = forms.DecimalField(label='Amount', min_value=0.01)
