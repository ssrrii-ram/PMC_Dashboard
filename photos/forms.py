from django import forms
from .models import SitePhoto


class SitePhotoForm(forms.ModelForm):

    class Meta:
        model = SitePhoto

        fields = '__all__'