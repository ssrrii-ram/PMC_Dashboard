from django import forms
from .models import Activity, Discipline, DisciplineProgress, MonthlyProgress


class DisciplineForm(forms.ModelForm):

    class Meta:
        model = Discipline
        fields = '__all__'
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class DisciplineProgressForm(forms.ModelForm):

    class Meta:
        model = DisciplineProgress

        fields = '__all__'
        widgets = {
            'report_date': forms.DateInput(attrs={'type': 'date'}),
        }


class MonthlyProgressForm(forms.ModelForm):

    class Meta:
        model = MonthlyProgress

        fields = '__all__'
        widgets = {
            'month': forms.DateInput(attrs={'type': 'date'}),
        }


class ActivityForm(forms.ModelForm):

    class Meta:
        model = Activity

        fields = '__all__'
        widgets = {
            'planned_start': forms.DateInput(attrs={'type': 'date'}),
            'planned_finish': forms.DateInput(attrs={'type': 'date'}),
            'actual_start': forms.DateInput(attrs={'type': 'date'}),
            'actual_finish': forms.DateInput(attrs={'type': 'date'}),
        }
