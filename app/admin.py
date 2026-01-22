from django.contrib import admin
from .models import (
    UserProfile,
    Agenda,
    ContactBericht,
    HulpAanvraag,
    Feedback,
    AuditLog,
    Skill,
    Project,
    Dienst,
    Aanmelding,
    Bericht,
    Availability,
    Wachtlijst,
)


@admin.register(ContactBericht)
class ContactBerichtAdmin(admin.ModelAdmin):
    list_display = ("voornaam", "achternaam", "email", "telefoonnummer", "woonplaats", "onderwerp", "verzonden_op")
    search_fields = ("voornaam", "achternaam", "email", "woonplaats", "onderwerp")


@admin.register(Agenda)
class AgendaAdmin(admin.ModelAdmin):
    list_display = ("titel", "datum", "begin_tijd", "eind_tijd", "user")
    list_filter = ("datum",)
    search_fields = ("titel", "user__username")


admin.site.register(UserProfile)
admin.site.register(HulpAanvraag)
admin.site.register(Feedback)
admin.site.register(AuditLog)
admin.site.register(Skill)
admin.site.register(Project)
admin.site.register(Dienst)
admin.site.register(Aanmelding)
admin.site.register(Bericht)
admin.site.register(Availability)
admin.site.register(Wachtlijst)
