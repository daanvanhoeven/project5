from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class Agenda(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agenda")
    titel = models.CharField(max_length=200)
    beschrijving = models.TextField(blank=True)
    datum = models.DateField()
    begin_tijd = models.TimeField(null=True, blank=True)
    eind_tijd = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.titel} ({self.datum})"


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


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    projectleider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='led_projects'
    )

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('projectleider', 'Projectleider'),
        ('vrijwilliger', 'Vrijwilliger'),
        ('hulpvrager', 'Hulpvrager'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='hulpvrager')
    phone = models.CharField(max_length=25, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    skills = models.ManyToManyField(Skill, blank=True)
    projects = models.ManyToManyField(Project, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class Dienst(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='diensten')
    titel = models.CharField(max_length=200)
    beschrijving = models.TextField(blank=True)
    datum = models.DateField()
    begin_tijd = models.TimeField()
    eind_tijd = models.TimeField()
    max_personen = models.IntegerField(default=1)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_diensten'
    )

    def __str__(self):
        return f"{self.titel} ({self.datum})"

    def spots_left(self):
        accepted = self.aanmeldingen.filter(status='accepted').count()
        return max(0, self.max_personen - accepted)

    # 🔥 DIT WAS JE PROBLEEM
    def is_full(self):
        return self.spots_left() <= 0


class Aanmelding(models.Model):
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    dienst = models.ForeignKey(Dienst, on_delete=models.CASCADE, related_name='aanmeldingen')
    status = models.CharField(max_length=20, default='pending')
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('volunteer', 'dienst')


class HulpAanvraag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    titel = models.CharField(max_length=200, blank=True)
    omschrijving = models.TextField()
    preferred_time = models.CharField(max_length=200, blank=True, null=True)
    required_skills = models.ManyToManyField(Skill, blank=True)
    status = models.CharField(max_length=20, default='nieuw')
    aangemaakt_op = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titel or "Geen titel"


class Bericht(models.Model):
    verzender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='verzonden')
    ontvanger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='ontvangen')
    hulpaanvraag = models.ForeignKey(HulpAanvraag, on_delete=models.CASCADE)
    boodschap = models.TextField()
    verzonden_op = models.DateTimeField(auto_now_add=True)


class Feedback(models.Model):
    hulpaanvraag = models.ForeignKey(HulpAanvraag, on_delete=models.CASCADE)

    gebruiker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    beoordeling = models.IntegerField(null=True, blank=True)

    opmerking = models.TextField(blank=True)

    aangemaakt_op = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback van {self.gebruiker or 'Onbekend'}"


class Availability(models.Model):
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    weekday = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    actie = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)


class Wachtlijst(models.Model):
    dienst = models.ForeignKey(Dienst, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    aangemeld_op = models.DateTimeField(auto_now_add=True)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)