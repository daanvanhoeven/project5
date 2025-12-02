from django import forms
from .models import ContactBericht

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactBericht
        fields = ["voornaam", "achternaam", "email", "telefoonnummer", "woonplaats", "onderwerp", "bericht"]
