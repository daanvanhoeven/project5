from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User

from .models import Agenda, ContactBericht, HulpAanvraag, UserProfile, Dienst, Aanmelding, Wachtlijst
from .forms import ContactForm
from .forms import HulpAanvraagForm, BerichtForm, FeedbackForm


def home(request):
    return render(request, "home.html")


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})


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


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        user = self.request.user

        if user.is_superuser or user.is_staff:
            return '/admin/'

        next_url = self.request.GET.get('next')
        if next_url:
            return next_url

        return '/agenda/mijn/'


def heeft_rol(user, rol):
    if not hasattr(user, 'userprofile'):
        return False
    return user.userprofile.role == rol


@login_required
def dashboard(request):
    if not heeft_rol(request.user, 'admin'):
        return redirect('home')

    totaal_aanvragen = HulpAanvraag.objects.count()
    afgerond = HulpAanvraag.objects.filter(status='afgerond').count()

    actieve_vrijwilligers = (
        Agenda.objects.values('user')
        .annotate(aantal=Count('id'))
        .order_by('-aantal')[:5]
    )

    return render(request, "dashboard.html", {
        "totaal": totaal_aanvragen,
        "afgerond": afgerond,
        "top_vrijwilligers": actieve_vrijwilligers
    })


# ====================
# GEBRUIKERSBEHEER
# ====================

@login_required
def beheer_gebruikers(request):
    if not heeft_rol(request.user, 'admin'):
        return redirect('home')

    gebruikers = User.objects.all().select_related("userprofile")

    return render(request, "admin/beheer_gebruikers.html", {
        "gebruikers": gebruikers
    })






@require_POST
@login_required
def wijzig_rol(request, user_id):
    if not heeft_rol(request.user, 'admin'):
        return redirect('home')

    nieuwe_rol = request.POST.get("rol")
    user = get_object_or_404(User, id=user_id)

    profiel = user.userprofile
    profiel.role = nieuwe_rol
    profiel.save()

    return redirect('beheer_gebruikers')


# ============ DIENSTEN / AANMELDINGEN ============

def lijst_diensten(request):
    diensten = Dienst.objects.filter(datum__gte=timezone.now().date()).order_by('datum', 'begin_tijd')
    return render(request, 'diensten/lijst.html', { 'diensten': diensten })


def dienst_detail(request, dienst_id):
    dienst = get_object_or_404(Dienst, id=dienst_id)
    user_aangemeld = None
    if request.user.is_authenticated:
        user_aangemeld = Aanmelding.objects.filter(volunteer=request.user, dienst=dienst).first()
    return render(request, 'diensten/detail.html', { 'dienst': dienst, 'user_aangemeld': user_aangemeld })


@require_POST
@login_required
def aanmeld_dienst(request, dienst_id):
    dienst = get_object_or_404(Dienst, id=dienst_id)
    # Prevent double registration
    existing = Aanmelding.objects.filter(volunteer=request.user, dienst=dienst).first()
    if existing:
        # If already on waitlist or accepted, do not duplicate
        return redirect('dienst_detail', dienst_id=dienst.id)

    if dienst.is_full():
        status = 'waitlist'
    else:
        status = 'accepted'

    Aanmelding.objects.create(volunteer=request.user, dienst=dienst, status=status)

    # Optional: If waitlist, create a Wachtlijst entry
    if status == 'waitlist':
        Wachtlijst.objects.create(dienst=dienst, user=request.user)

    return redirect('dienst_detail', dienst_id=dienst.id)


@login_required
def create_hulpaanvraag(request):
    if request.method == 'POST':
        form = HulpAanvraagForm(request.POST)
        if form.is_valid():
            hulp = form.save(commit=False)
            hulp.user = request.user
            hulp.save()
            form.save_m2m()
            return redirect('mijn_hulpaanvragen')
    else:
        form = HulpAanvraagForm()
    return render(request, 'hulpaanvraag/create.html', {'form': form})


@login_required
def mijn_hulpaanvragen(request):
    aanvragen = HulpAanvraag.objects.filter(user=request.user).order_by('-aangemaakt_op')
    return render(request, 'hulpaanvraag/mijn_aanvragen.html', {'aanvragen': aanvragen})


@login_required
def hulpaanvraag_detail(request, aanvraag_id):
    aanvraag = get_object_or_404(HulpAanvraag, id=aanvraag_id)
    if request.method == 'POST':
        form = BerichtForm(request.POST)
        if form.is_valid():
            bericht = form.save(commit=False)
            bericht.verzender = request.user
            bericht.hulpaanvraag = aanvraag
            bericht.save()
            return redirect('hulpaanvraag_detail', aanvraag_id=aanvraag.id)
    else:
        form = BerichtForm()
    return render(request, 'hulpaanvraag/detail.html', {'aanvraag': aanvraag, 'form': form})


from .forms import HulpAanvraagForm

@login_required
def nieuwe_aanvraag(request):
    if not heeft_rol(request.user, 'hulpvrager'):
        return redirect('home')

    if request.method == "POST":
        form = HulpAanvraagForm(request.POST)
        if form.is_valid():
            aanvraag = form.save(commit=False)
            aanvraag.user = request.user
            aanvraag.save()
            return redirect('mijn_aanvragen')
    else:
        form = HulpAanvraagForm()

    return render(request, "aanvragen/nieuw.html", {"form": form})


from .forms import HulpAanvraagForm

@login_required
def nieuwe_aanvraag(request):
    if not heeft_rol(request.user, 'hulpvrager'):
        return redirect('home')

    if request.method == "POST":
        form = HulpAanvraagForm(request.POST)
        if form.is_valid():
            aanvraag = form.save(commit=False)
            aanvraag.user = request.user
            aanvraag.save()
            return redirect('mijn_aanvragen')
    else:
        form = HulpAanvraagForm()

    return render(request, "aanvragen/nieuw.html", {"form": form})


@login_required
def mijn_aanvragen(request):
    aanvragen = HulpAanvraag.objects.filter(user=request.user)
    return render(request, "aanvragen/mijn.html", {"aanvragen": aanvragen})


@login_required
def wijzig_aanvraag(request, aanvraag_id):
    aanvraag = get_object_or_404(HulpAanvraag, id=aanvraag_id, user=request.user)

    if request.method == "POST":
        form = HulpAanvraagForm(request.POST, instance=aanvraag)
        if form.is_valid():
            form.save()
            return redirect("mijn_aanvragen")
    else:
        form = HulpAanvraagForm(instance=aanvraag)

    return render(request, "aanvragen/wijzig.html", {"form": form})


from django.http import HttpResponseForbidden
from .utils import user_has_role

def admin_dashboard(request):
    if not user_has_role(request.user, 'admin'):
        return HttpResponseForbidden("Geen toegang")

    return render(request, 'admin/dashboard.html')


from django.http import HttpResponseForbidden
from .utils import user_has_role

def admin_dashboard(request):
    if not user_has_role(request.user, 'admin'):
        return HttpResponseForbidden("Geen toegang")

    return render(request, 'admin/dashboard.html')
