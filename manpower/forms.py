from django import forms
from .models import Manpower

class ManpowerForm(forms.ModelForm):
    class Meta:
        model = Manpower
        fields = '__all__'
        widgets = {
            'report_date': forms.DateInput(attrs={'type': 'date'}),
        }
