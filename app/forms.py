from django import forms
from .models import ContactBericht, HulpAanvraag, Bericht, Feedback, Dienst

# ====================
# Contactformulier
# ====================
class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactBericht
        fields = [
            "voornaam",
            "achternaam",
            "email",
            "telefoonnummer",
            "woonplaats",
            "onderwerp",
            "bericht",
        ]


# ====================
# Hulpaanvraag
# ====================
class HulpAanvraagForm(forms.ModelForm):
    class Meta:
        model = HulpAanvraag
        fields = ["titel", "omschrijving", "preferred_time", "required_skills"]


# ====================
# Bericht
# ====================
class BerichtForm(forms.ModelForm):
    class Meta:
        model = Bericht
        fields = ["boodschap"]


# ====================
# Feedback
# ====================
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["beoordeling", "opmerking"]


# ====================
# Dienst (voor admin CRUD)
# ====================
class DienstForm(forms.ModelForm):
    class Meta:
        model = Dienst
        fields = [
            "project",
            "hulpaanvraag",
            "titel",
            "beschrijving",
            "datum",
            "begin_tijd",
            "eind_tijd",
            "max_personen"
        ]
        widgets = {
            "datum": forms.DateInput(attrs={"type": "date"}),
            "begin_tijd": forms.TimeInput(attrs={"type": "time"}),
            "eind_tijd": forms.TimeInput(attrs={"type": "time"}),
        }