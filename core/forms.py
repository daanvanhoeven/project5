from django import forms
from .models import ContactBericht, HulpAanvraag

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactBericht
        fields = ["naam", "email", "bericht"]


class HulpAanvraagForm(forms.ModelForm):
    class Meta:
        model = HulpAanvraag
        fields = ["titel", "omschrijving", "status"]
