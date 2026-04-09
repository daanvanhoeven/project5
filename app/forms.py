from django import forms
from .models import ContactBericht
from .models import HulpAanvraag, Bericht, Feedback


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactBericht
        fields = ["voornaam", "achternaam", "email", "telefoonnummer", "woonplaats", "onderwerp", "bericht"]


class HulpAanvraagForm(forms.ModelForm):
    class Meta:
        model = HulpAanvraag
        fields = ["titel", "omschrijving", "preferred_time", "required_skills"]


class BerichtForm(forms.ModelForm):
    class Meta:
        model = Bericht
        fields = ["boodschap"]


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["score", "commentaar"]


class HulpAanvraagForm(forms.ModelForm):
    class Meta:
        model = HulpAanvraag
        fields = ["omschrijving"]
