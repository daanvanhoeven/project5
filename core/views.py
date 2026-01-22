from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User

from .models import Agenda, ContactBericht, HulpAanvraag, UserProfile
from .forms import ContactForm, HulpAanvraagForm


def home(request):
    return render(request, "home.html")


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, role="gebruiker")
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})


class CustomLoginView(LoginView):
    template_name = "registration/login.html"

    def get_success_url(self):
        user = self.request.user

        if user.is_superuser or user.is_staff:
            return "/admin/"

        if user.userprofile.role == "admin":
            return "/dashboard/"

        return "/agenda/mijn/"


@login_required
def mijn_agenda(request):
    afspraken = Agenda.objects.filter(user=request.user)
    return render(request, "agenda/mijn_agenda.html", {"agenda_items": afspraken})


def contactformulier(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("contactformulier")
    else:
        form = ContactForm()
    return render(request, "contactformulier.html", {"form": form})


# -----------------
# HULPAANVRAGEN
# -----------------

@login_required
def mijn_aanvragen(request):
    aanvragen = HulpAanvraag.objects.filter(gebruiker=request.user)
    return render(request, "aanvragen/mijn_aanvragen.html", {"aanvragen": aanvragen})


@login_required
def nieuwe_aanvraag(request):
    if request.method == "POST":
        form = HulpAanvraagForm(request.POST)
        if form.is_valid():
            aanvraag = form.save(commit=False)
            aanvraag.gebruiker = request.user
            aanvraag.save()
            return redirect("mijn_aanvragen")
    else:
        form = HulpAanvraagForm()
    return render(request, "aanvragen/nieuw.html", {"form": form})


@login_required
def wijzig_aanvraag(request, aanvraag_id):
    aanvraag = get_object_or_404(HulpAanvraag, id=aanvraag_id, gebruiker=request.user)

    if request.method == "POST":
        form = HulpAanvraagForm(request.POST, instance=aanvraag)
        if form.is_valid():
            form.save()
            return redirect("mijn_aanvragen")
    else:
        form = HulpAanvraagForm(instance=aanvraag)

    return render(request, "aanvragen/wijzig.html", {"form": form})


# -----------------
# ADMIN
# -----------------

def heeft_rol(user, rol):
    if not hasattr(user, "userprofile"):
        return False
    return user.userprofile.role == rol


@login_required
def dashboard(request):
    if not heeft_rol(request.user, "admin"):
        return redirect("home")

    totaal_aanvragen = HulpAanvraag.objects.count()
    afgerond = HulpAanvraag.objects.filter(status="afgerond").count()

    actieve_vrijwilligers = (
        Agenda.objects.values("user")
        .annotate(aantal=Count("id"))
        .order_by("-aantal")[:5]
    )

    return render(request, "dashboard.html", {
        "totaal": totaal_aanvragen,
        "afgerond": afgerond,
        "top_vrijwilligers": actieve_vrijwilligers,
    })


@login_required
def beheer_gebruikers(request):
    if not heeft_rol(request.user, "admin"):
        return redirect("home")

    gebruikers = User.objects.all().select_related("userprofile")

    return render(request, "admin/beheer_gebruikers.html", {"gebruikers": gebruikers})


@require_POST
@login_required
def wijzig_rol(request, user_id):
    if not heeft_rol(request.user, "admin"):
        return redirect("home")

    nieuwe_rol = request.POST.get("rol")
    user = get_object_or_404(User, id=user_id)

    profiel = user.userprofile
    profiel.role = nieuwe_rol
    profiel.save()

    return redirect("beheer_gebruikers")
