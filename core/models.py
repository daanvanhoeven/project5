from django.db import models
from django.contrib.auth.models import User


class Agenda(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    datum = models.DateField()
    tijd = models.TimeField()
    omschrijving = models.TextField()

    def __str__(self):
        return f"{self.user.username} – {self.datum} {self.tijd}"


class ContactBericht(models.Model):
    naam = models.CharField(max_length=100)
    email = models.EmailField()
    bericht = models.TextField()
    datum = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bericht van {self.naam}"


class HulpAanvraag(models.Model):
    STATUSSEN = [
        ('open', 'Open'),
        ('bezig', 'Bezig'),
        ('afgerond', 'Afgerond'),
    ]

    gebruiker = models.ForeignKey(User, on_delete=models.CASCADE)
    titel = models.CharField(max_length=200)
    omschrijving = models.TextField()
    status = models.CharField(max_length=20, choices=STATUSSEN, default='open')

    def __str__(self):
        return f"{self.titel} ({self.status})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=30, default="gebruiker")  # admin/vrijwilliger/gebruiker

    def __str__(self):
        return f"{self.user.username} – {self.role}"


class Dienst(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='diensten'
    )

    titel = models.CharField(max_length=200)
    beschrijving = models.TextField(blank=True)
    datum = models.DateField()
    begin_tijd = models.TimeField()
    eind_tijd = models.TimeField()

    max_personen = models.PositiveIntegerField(default=1)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='aangemaakte_diensten'
    )

    def __str__(self):
        return f"{self.titel} - {self.datum}"

    # ---- Extra functionaliteit ----

    def aantal_aanmeldingen(self):
        """Vrijwilligers die geaccepteerd zijn."""
        return self.aanmeldingen.filter(status='accepted').count()

    def spots_left(self):
        return max(0, self.max_personen - self.aantal_aanmeldingen())

    def is_full(self):
        return self.spots_left() == 0

    def percentage_bezetting(self):
        if self.max_personen == 0:
            return 0
        return int((self.aantal_aanmeldingen() / self.max_personen) * 100)


class Aanmelding(models.Model):
    STATUS_CHOICES = [
        ('pending', 'In afwachting'),
        ('accepted', 'Geaccepteerd'),
        ('rejected', 'Afgewezen'),
        ('waitlist', 'Wachtlijst'),
    ]

    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='aanmeldingen'
    )

    dienst = models.ForeignKey(
        Dienst,
        on_delete=models.CASCADE,
        related_name='aanmeldingen'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('volunteer', 'dienst')

    def __str__(self):
        return f"{self.volunteer.username} -> {self.dienst.titel} ({self.status})"
