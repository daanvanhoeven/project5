from django.db import models
from django.contrib.auth.models import User

class Agenda(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="agenda")
    titel = models.CharField(max_length=200)
    beschrijving = models.TextField(blank=True)
    datum = models.DateField()
    begin_tijd = models.TimeField(null=True, blank=True)
    eind_tijd = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.titel} ({self.datum} {self.begin_tijd}-{self.eind_tijd}) - {self.user.username}"

class ContactBericht(models.Model):
    voornaam = models.CharField(max_length=100)
    achternaam = models.CharField(max_length=100)
    email = models.EmailField()
    telefoonnummer = models.CharField(max_length=20, blank=True, null=True)
    woonplaats = models.CharField(max_length=100, blank=True, null=True)
    onderwerp = models.CharField(max_length=200)
    bericht = models.TextField()
    verzonden_op = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.voornaam} {self.achternaam} - {self.onderwerp}"