from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User

from .models import (
    Agenda, ContactBericht, HulpAanvraag,
    UserProfile, Dienst, Aanmelding, Wachtlijst
)
from .forms import ContactForm, HulpAanvraagForm, BerichtForm


# ====================
# BASIS PAGINA'S
# ====================

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


# ====================
# HELPERS
# ====================

def heeft_rol(user, rol):
    return hasattr(user, "userprofile") and user.userprofile.role == rol


# ====================
# AGENDA
# ====================

@login_required
def mijn_agenda(request):
    afspraken = Agenda.objects.filter(user=request.user)
    return render(request, "agenda/mijn_agenda.html", {"agenda_items": afspraken})


# ====================
# CONTACT
# ====================

def contactformulier(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("contactformulier")
    else:
        form = ContactForm()
    return render(request, "contactformulier.html", {"form": form})


# ====================
# ADMIN DASHBOARD
# ====================

@login_required
def dashboard(request):
    if not heeft_rol(request.user, "admin"):
        return redirect("home")

    totaal = HulpAanvraag.objects.count()
    afgerond = HulpAanvraag.objects.filter(status="afgerond").count()

    top_vrijwilligers = (
        Agenda.objects.values("user")
        .annotate(aantal=Count("id"))
        .order_by("-aantal")[:5]
    )

    return render(request, "dashboard.html", {
        "totaal": totaal,
        "afgerond": afgerond,
        "top_vrijwilligers": top_vrijwilligers
    })


# ====================
# GEBRUIKERSBEHEER
# ====================

@login_required
def beheer_gebruikers(request):
    if not heeft_rol(request.user, "admin"):
        return redirect("home")

    gebruikers = User.objects.select_related("userprofile").all()
    return render(request, "admin/beheer_gebruikers.html", {"gebruikers": gebruikers})


@require_POST
@login_required
def wijzig_rol(request, user_id):
    if not heeft_rol(request.user, "admin"):
        return redirect("home")

    user = get_object_or_404(User, id=user_id)
    user.userprofile.role = request.POST.get("rol")
    user.userprofile.save()

    return redirect("beheer_gebruikers")


# ====================
# HULPAANVRAGEN
# ====================

@login_required
def create_hulpaanvraag(request):
    if request.method == "POST":
        form = HulpAanvraagForm(request.POST)
        if form.is_valid():
            aanvraag = form.save(commit=False)
            aanvraag.user = request.user
            aanvraag.save()
            return redirect("mijn_hulpaanvragen")
    else:
        form = HulpAanvraagForm()
    return render(request, "hulpaanvraag/create.html", {"form": form})


@login_required
def mijn_hulpaanvragen(request):
    aanvragen = HulpAanvraag.objects.filter(user=request.user)
    return render(request, "hulpaanvraag/mijn_aanvragen.html", {"aanvragen": aanvragen})


@login_required
def hulpaanvraag_detail(request, aanvraag_id):
    aanvraag = get_object_or_404(HulpAanvraag, id=aanvraag_id)

    if request.method == "POST":
        form = BerichtForm(request.POST)
        if form.is_valid():
            bericht = form.save(commit=False)
            bericht.verzender = request.user
            bericht.hulpaanvraag = aanvraag
            bericht.save()
            return redirect("hulpaanvraag_detail", aanvraag_id=aanvraag.id)
    else:
        form = BerichtForm()

    return render(request, "hulpaanvraag/detail.html", {
        "aanvraag": aanvraag,
        "form": form
    })


# ====================
# PROFIEL
# ====================

@login_required
def profiel(request):
    return render(request, "profiel.html", {
        "user": request.user
    })


@login_required
def lijst_diensten(request):
    diensten = Dienst.objects.all()
    return render(request, "diensten/lijst.html", {
        "diensten": diensten
    })
