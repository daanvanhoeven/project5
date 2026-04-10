from django.contrib import admin
from .models import Agenda
from .models import ContactBericht
from .models import Feedback

admin.site.register(Feedback)


admin.site.register(Agenda)

@admin.register(ContactBericht)
class ContactBerichtAdmin(admin.ModelAdmin):
    list_display = ("voornaam", "achternaam", "email", "telefoonnummer", "woonplaats", "onderwerp", "verzonden_op")
    search_fields = ("voornaam", "achternaam", "email", "woonplaats", "onderwerp")

