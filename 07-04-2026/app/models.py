from django.db import models
from django.conf import settings
from django.utils import timezone
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


# ---- Phase 1 models (consolidated and Dutch naming where appropriate) ----


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    projectleider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='led_projects')

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
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_diensten')

    def __str__(self):
        return f"{self.titel} ({self.datum})"

    def spots_left(self):
        accepted = self.aanmeldingen.filter(status='accepted').count()
        return max(0, self.max_personen - accepted)

    def is_full(self):
        return self.spots_left() <= 0


class Aanmelding(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('waitlist', 'Waitlist'),
    ]
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='aanmeldingen')
    dienst = models.ForeignKey(Dienst, on_delete=models.CASCADE, related_name='aanmeldingen')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('volunteer', 'dienst')

    def __str__(self):
        return f"{self.volunteer.username} -> {self.dienst.titel} ({self.status})"


class HulpAanvraag(models.Model):
    STATUS_CHOICES = [
        ('nieuw', 'Nieuw'),
        ('in_behandeling', 'In behandeling'),
        ('ingepland', 'Ingepland'),
        ('afgerond', 'Afgerond'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hulpaanvragen')
    titel = models.CharField(max_length=200, blank=True)
    omschrijving = models.TextField()
    preferred_time = models.CharField(max_length=200, blank=True, null=True)
    required_skills = models.ManyToManyField(Skill, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='nieuw')
    aangemaakt_op = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.titel or 'Geen titel'} ({self.get_status_display()})"


class Bericht(models.Model):
    verzender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='verzonden_berichten')
    ontvanger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='ontvangen_berichten')
    hulpaanvraag = models.ForeignKey(HulpAanvraag, on_delete=models.CASCADE, related_name='berichten')
    boodschap = models.TextField()
    verzonden_op = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bericht van {self.verzender} op {self.verzonden_op}"


class Feedback(models.Model):
    hulpaanvraag = models.OneToOneField(HulpAanvraag, on_delete=models.CASCADE, related_name='feedback')
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    commentaar = models.TextField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback gebaseerd op {self.hulpaanvraag} - {self.score or 'geen score'}"


class Availability(models.Model):
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='availabilities')
    weekday = models.IntegerField(choices=[(i, str(i)) for i in range(7)])
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.volunteer.username} beschikbaar op {self.weekday} {self.start_time}-{self.end_time}"


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    actie = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.actie}"


class Wachtlijst(models.Model):
    dienst = models.ForeignKey(Dienst, on_delete=models.CASCADE, related_name='wachtlijst')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    aangemeld_op = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} in wachtlijst voor {self.dienst.titel}"


# Signals: make sure a UserProfile exists when a user is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
 
