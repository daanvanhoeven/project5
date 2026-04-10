from django import forms
from .models import ContactBericht, HulpAanvraag, Bericht, Feedback, Dienst
from .utils import availability_has_period_fields

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


class AvailabilityForm(forms.Form):
    WEEKDAY_CHOICES = [
        (1, "Zondag"),
        (2, "Maandag"),
        (3, "Dinsdag"),
        (4, "Woensdag"),
        (5, "Donderdag"),
        (6, "Vrijdag"),
        (7, "Zaterdag"),
    ]

    weekday = forms.ChoiceField(
        choices=WEEKDAY_CHOICES,
        label="Dag van de week",
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time"}),
        label="Starttijd",
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"type": "time"}),
        label="Eindtijd",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if availability_has_period_fields():
            self.fields["valid_from"] = forms.DateField(
                widget=forms.DateInput(attrs={"type": "date"}),
                label="Vanaf datum",
            )
            self.fields["valid_until"] = forms.DateField(
                widget=forms.DateInput(attrs={"type": "date"}),
                label="Tot en met",
            )

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        valid_from = cleaned_data.get("valid_from")
        valid_until = cleaned_data.get("valid_until")

        if start_time and end_time and start_time >= end_time:
            self.add_error("end_time", "De eindtijd moet later zijn dan de starttijd.")

        if valid_from and valid_until and valid_from > valid_until:
            self.add_error("valid_until", "De einddatum moet op of na de startdatum liggen.")

        return cleaned_data
