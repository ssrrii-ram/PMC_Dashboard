from django import forms
from .models import CashFlow


class CashFlowForm(forms.ModelForm):

    class Meta:
        model = CashFlow

        fields = '__all__'
        widgets = {
            'month': forms.DateInput(attrs={'type': 'date'}),
        }
