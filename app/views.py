from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.utils import timezone
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.models import User
from datetime import date, datetime, time, timedelta
from .models import Skill
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import User
from .models import Dienst, Aanmelding
from .utils import (
    availability_has_period_fields,
    create_availability_for_user,
    delete_availability_for_user,
    ensure_user_profile,
    get_user_role,
    heeft_rol,
    list_active_availability,
    list_user_availability,
)
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    Agenda, ContactBericht, HulpAanvraag,
    UserProfile, Dienst, Aanmelding, Wachtlijst,
    Project
)

from .forms import (
    AvailabilityForm,
    ContactForm,
    HulpAanvraagForm,
    BerichtForm,
    DienstForm,
    FeedbackForm
)


def get_relevante_diensten_voor_vrijwilliger(user):
    vandaag = timezone.localdate()
    beschikbaarheden = list_active_availability(user, vandaag)

    diensten = Dienst.objects.none()

    for beschikbaarheid in beschikbaarheden:
        diensten = diensten | Dienst.objects.filter(
            datum__gte=vandaag,
            datum__week_day=beschikbaarheid.weekday,
            begin_tijd__gte=beschikbaarheid.start_time,
            eind_tijd__lte=beschikbaarheid.end_time,
        )

    return diensten.order_by("datum", "begin_tijd").distinct()


def get_vrijwilliger_skill_namen(vrijwilliger):
    profiel = ensure_user_profile(vrijwilliger)
    return [skill.name for skill in profiel.skills.all().order_by("name")]


def vrijwilliger_matcht_dienst(vrijwilliger, dienst):
    profiel = ensure_user_profile(vrijwilliger)
    vereiste_skill_ids = set()

    if dienst.hulpaanvraag_id:
        vereiste_skill_ids = set(
            dienst.hulpaanvraag.required_skills.values_list("id", flat=True)
        )

    vrijwilliger_skill_ids = set(profiel.skills.values_list("id", flat=True))
    skill_match = not vereiste_skill_ids or vereiste_skill_ids.issubset(vrijwilliger_skill_ids)

    beschikbaarheden = list_active_availability(vrijwilliger, dienst.datum)
    availability_match = any(
        beschikbaarheid.weekday == ((dienst.datum.isoweekday() % 7) + 1)
        and beschikbaarheid.start_time <= dienst.begin_tijd
        and beschikbaarheid.end_time >= dienst.eind_tijd
        for beschikbaarheid in beschikbaarheden
    )

    return {
        "skill_match": skill_match,
        "availability_match": availability_match,
        "overall_match": skill_match and availability_match,
        "skills": get_vrijwilliger_skill_namen(vrijwilliger),
    }


def build_dienst_status(dienst):
    accepted_count = dienst.aanmeldingen.filter(status="accepted").count()
    waitlist_count = dienst.aanmeldingen.filter(status="waitlist").count()
    min_personen = 1
    spots_left = max(dienst.max_personen - accepted_count, 0)
    meldingen = []

    if accepted_count < min_personen:
        meldingen.append({
            "niveau": "danger",
            "tekst": "Nog niet genoeg vrijwilligers ingepland.",
        })
    elif spots_left == 1:
        meldingen.append({
            "niveau": "warning",
            "tekst": "Bijna vol: nog 1 plek beschikbaar.",
        })

    if spots_left == 0:
        meldingen.append({
            "niveau": "secondary",
            "tekst": "Dienst is vol.",
        })

    if waitlist_count:
        meldingen.append({
            "niveau": "info",
            "tekst": f"{waitlist_count} vrijwilliger(s) op de wachtlijst.",
        })

    return {
        "dienst": dienst,
        "accepted_count": accepted_count,
        "waitlist_count": waitlist_count,
        "spots_left": spots_left,
        "min_personen": min_personen,
        "meldingen": meldingen,
        "onderbezet": accepted_count < min_personen,
        "bijna_vol": spots_left == 1,
        "vol": spots_left == 0,
    }


@login_required
def home(request):

    relevante_diensten = None
    aangemeld_ids = []
    role = get_user_role(request.user)

    # Alleen voor vrijwilligers
    if role == "vrijwilliger":
        diensten = get_relevante_diensten_voor_vrijwilliger(request.user)

        aangemeld_ids = Aanmelding.objects.filter(
            volunteer=request.user
        ).values_list("dienst_id", flat=True)

        relevante_diensten = diensten

    return render(request, "home.html", {
        "relevante_diensten": relevante_diensten,
        "aangemeld_ids": aangemeld_ids if role == "vrijwilliger" else []
    })






def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()

            profile = ensure_user_profile(user)
            profile.role = "vrijwilliger"
            profile.save()

            login(request, user)
            return redirect("home")

    else:
        form = UserCreationForm()

    return render(
        request,
        "registration/register.html",
        {"form": form}
    )


class CustomLoginView(LoginView):
    template_name = "registration/login.html"

    def get_success_url(self):
        user = self.request.user
        role = get_user_role(user, default="hulpvrager", create_missing=True)
        if user.is_superuser or user.is_staff:
            return "/admin/"
        if role == "admin":
            return "/dashboard/"
        return "/"


# ====================
# HELPERS
# ====================

def heeft_rol(user, rol):
    return get_user_role(user) == rol


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
    for gebruiker in gebruikers:
        ensure_user_profile(gebruiker)
    return render(request, "admin/beheer_gebruikers.html", {"gebruikers": gebruikers})


@require_POST
@login_required
def wijzig_rol(request, user_id):
    if not heeft_rol(request.user, "admin"):
        return redirect("home")

    user = get_object_or_404(User, id=user_id)
    profile = ensure_user_profile(user)
    profile.role = request.POST.get("rol")
    profile.save()

    return redirect("beheer_gebruikers")


@require_POST
@login_required
def toggle_user_active(request, user_id):
    if not heeft_rol(request.user, "admin"):
        return redirect("home")

    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])

    return redirect("beheer_gebruikers")


# ====================
# HULPAANVRAGEN
# ====================



@login_required
def create_hulpaanvraag(request):
    if not heeft_rol(request.user, "hulpvrager"):
        # Als gebruiker geen hulpvrager is, mag hij niet aanmaken
        return redirect("home")  # of toon een foutmelding

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


@login_required
def dienst_detail(request, dienst_id):
    dienst = get_object_or_404(
        Dienst.objects.select_related("project", "hulpaanvraag").prefetch_related(
            "hulpaanvraag__required_skills",
            "aanmeldingen__volunteer__userprofile__skills",
        ),
        id=dienst_id,
    )

    aanmelding = Aanmelding.objects.filter(
        volunteer=request.user,
        dienst=dienst
    ).first()

    vrijwilligers = User.objects.filter(
        userprofile__role="vrijwilliger"
    ).prefetch_related("userprofile__skills")

    toegewezen_vrijwilligers = dienst.aanmeldingen.filter(
        status="accepted"
    ).select_related("volunteer")
    wachtlijst = dienst.aanmeldingen.filter(
        status="waitlist"
    ).select_related("volunteer")

    kandidaat_vrijwilligers = []
    al_geplande_ids = set(dienst.aanmeldingen.values_list("volunteer_id", flat=True))

    for vrijwilliger in vrijwilligers:
        match_info = vrijwilliger_matcht_dienst(vrijwilliger, dienst)
        kandidaat_vrijwilligers.append({
            "user": vrijwilliger,
            "skills": match_info["skills"],
            "skill_match": match_info["skill_match"],
            "availability_match": match_info["availability_match"],
            "overall_match": match_info["overall_match"],
            "already_assigned": vrijwilliger.id in al_geplande_ids,
        })

    kandidaat_vrijwilligers.sort(
        key=lambda item: (
            item["already_assigned"],
            not item["overall_match"],
            not item["skill_match"],
            item["user"].username.lower(),
        )
    )

    return render(request, "diensten/detail.html", {
        "dienst": dienst,
        "aanmelding": aanmelding,
        "vrijwilligers": vrijwilligers,
        "kandidaat_vrijwilligers": kandidaat_vrijwilligers,
        "toegewezen_vrijwilligers": toegewezen_vrijwilligers,
        "wachtlijst": wachtlijst,
        "required_skills": dienst.hulpaanvraag.required_skills.all() if dienst.hulpaanvraag_id else [],
        "dienst_status": build_dienst_status(dienst),
    })

@login_required
@require_POST
def aanmelden_dienst(request, dienst_id):
    dienst = get_object_or_404(Dienst, id=dienst_id)

    # Check of gebruiker al aangemeld is
    bestaande_aanmelding = Aanmelding.objects.filter(
        volunteer=request.user,
        dienst=dienst
    ).first()

    if bestaande_aanmelding:
        return redirect("dienst_detail", dienst_id=dienst.id)

    # Check of dienst vol is
    if dienst.is_full():

        Aanmelding.objects.create(
            volunteer=request.user,
            dienst=dienst,
            status="waitlist"
        )

    else:

        Aanmelding.objects.create(
            volunteer=request.user,
            dienst=dienst,
            status="accepted"
        )

    return redirect("dienst_detail", dienst_id=dienst.id)



@login_required
@require_POST
def afmelden_dienst(request, dienst_id):
    dienst = get_object_or_404(Dienst, id=dienst_id)

    aanmelding = Aanmelding.objects.filter(
        volunteer=request.user,
        dienst=dienst
    ).first()

    if aanmelding:
        aanmelding.delete()

    return redirect("dienst_detail", dienst_id=dienst.id)


from .forms import DienstForm
from django.contrib import messages

def dienst_create(request):
    if get_user_role(request.user) not in ["admin", "projectleider"]:
        return redirect("home")

    if request.method == "POST":
        form = DienstForm(request.POST)
        if form.is_valid():
            dienst = form.save(commit=False)
            dienst.created_by = request.user

        
            aanvraag_id = request.POST.get("hulpaanvraag")
            if aanvraag_id:
                dienst.hulpaanvraag = HulpAanvraag.objects.get(id=aanvraag_id)

            dienst.save()
            return redirect("lijst_diensten")

    else:
        form = DienstForm()

    aanvragen = HulpAanvraag.objects.filter(status="nieuw")

    return render(request, "diensten/form.html", {
        "form": form,
        "aanvragen": aanvragen
    })

@login_required
def dienst_update(request, dienst_id):
    if not heeft_rol(request.user, "admin"):
        return redirect("home")

    dienst = get_object_or_404(Dienst, id=dienst_id)

    if request.method == "POST":
        form = DienstForm(request.POST, instance=dienst)
        if form.is_valid():
            form.save()
            messages.success(request, "Dienst succesvol bijgewerkt!")
            return redirect("dienst_detail", dienst_id=dienst.id)
    else:
        form = DienstForm(instance=dienst)

    return render(request, "diensten/form.html", {"form": form, "title": "Bewerk dienst"})

@login_required
@require_POST
def dienst_delete(request, dienst_id):
    if not heeft_rol(request.user, "admin"):
        return redirect("home")

    dienst = get_object_or_404(Dienst, id=dienst_id)
    dienst.delete()
    messages.success(request, "Dienst succesvol verwijderd!")
    return redirect("lijst_diensten")

@login_required
def admin_overzicht_diensten(request):
    if not heeft_rol(request.user, "admin"):
        return redirect("home")

    diensten = Dienst.objects.all().order_by("datum", "begin_tijd")
    return render(request, "diensten/admin_overzicht.html", {"diensten": diensten})


from django.contrib import messages

@login_required
@require_POST
def hulpaanvraag_delete(request, aanvraag_id):

    aanvraag = get_object_or_404(
        HulpAanvraag,
        id=aanvraag_id,
        user=request.user
    )

    aanvraag.delete()

    messages.success(
        request,
        "Je hulpaanvraag is geannuleerd."
    )

    return redirect("mijn_hulpaanvragen")


@login_required
def hulpaanvraag_update(request, aanvraag_id):

    aanvraag = get_object_or_404(
        HulpAanvraag,
        id=aanvraag_id,
        user=request.user
    )

    if request.method == "POST":

        form = HulpAanvraagForm(
            request.POST,
            instance=aanvraag
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Je hulpaanvraag is bijgewerkt."
            )

            return redirect(
                "mijn_hulpaanvragen"
            )

    else:

        form = HulpAanvraagForm(
            instance=aanvraag
        )

    return render(
        request,
        "hulpaanvraag/form.html",
        {
            "form": form,
            "title": "Bewerk hulpaanvraag"
        }
    )

from .models import HulpAanvraag, Feedback
from .forms import FeedbackForm
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required


@login_required
def geef_feedback(request, aanvraag_id):
    aanvraag = get_object_or_404(HulpAanvraag, id=aanvraag_id)

    # alleen eigenaar mag feedback geven
    if aanvraag.user != request.user:
        return redirect("home")

    # alleen als afgerond
    if aanvraag.status != "afgerond":
        return redirect("mijn_aanvragen")

    # check of al feedback bestaat
    if hasattr(aanvraag, "feedback"):
        return redirect("mijn_aanvragen")

    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.hulpaanvraag = aanvraag
            feedback.gebruiker = request.user
            feedback.save()
            return redirect("mijn_aanvragen")
    else:
        form = FeedbackForm()

    return render(request, "feedback.html", {"form": form})

@login_required
def projectleider_dashboard(request):
    if not heeft_rol(request.user, "projectleider") and not heeft_rol(request.user, "admin"):
        return redirect("home")

    diensten = Dienst.objects.select_related(
        "project",
        "hulpaanvraag",
    ).prefetch_related(
        "hulpaanvraag__required_skills",
        "aanmeldingen",
    ).order_by("datum", "begin_tijd")

    dienst_statussen = [build_dienst_status(dienst) for dienst in diensten]

    te_weinig = [item for item in dienst_statussen if item["onderbezet"]]
    bijna_vol = [item for item in dienst_statussen if item["bijna_vol"]]
    vol = [item for item in dienst_statussen if item["vol"]]

    meldingen = []
    for item in dienst_statussen:
        for melding in item["meldingen"]:
            meldingen.append({
                "dienst": item["dienst"],
                "niveau": melding["niveau"],
                "tekst": melding["tekst"],
            })

    vrijwilligers = User.objects.filter(
        userprofile__role="vrijwilliger"
    ).prefetch_related("userprofile__skills")

    vrijwilligers_overzicht = [
        {
            "user": vrijwilliger,
            "skills": get_vrijwilliger_skill_namen(vrijwilliger),
        }
        for vrijwilliger in vrijwilligers
    ]

    return render(request, "projectleider/dashboard.html", {
        "diensten": diensten,
        "vrijwilligers": vrijwilligers,
        "vrijwilligers_overzicht": vrijwilligers_overzicht,
        "dienst_statussen": dienst_statussen,
        "te_weinig": te_weinig,
        "bijna_vol": bijna_vol,
        "vol": vol,
        "meldingen": meldingen,
    })

@login_required
def vrijwilligers_filter(request):
    if not heeft_rol(request.user, "projectleider"):
        return redirect("home")

    skill_id = request.GET.get("skill")
    zoekterm = request.GET.get("q", "").strip()

    vrijwilligers = User.objects.filter(
        userprofile__role="vrijwilliger"
    ).prefetch_related("userprofile__skills")

    if skill_id:
        vrijwilligers = vrijwilligers.filter(
            userprofile__skills__id=skill_id
        )

    if zoekterm:
        vrijwilligers = vrijwilligers.filter(username__icontains=zoekterm)

    skills = Skill.objects.all()

    vrijwilligers_data = [
        {
            "user": vrijwilliger,
            "skills": get_vrijwilliger_skill_namen(vrijwilliger),
            "availability_count": len(list_user_availability(vrijwilliger)),
        }
        for vrijwilliger in vrijwilligers.distinct()
    ]

    return render(request, "projectleider/vrijwilligers.html", {
        "vrijwilligers": vrijwilligers_data,
        "skills": skills,
        "selected_skill": str(skill_id or ""),
        "zoekterm": zoekterm,
    })

def stuur_status_mail(aanmelding):
    vrijwilliger = aanmelding.volunteer
    dienst = aanmelding.dienst

    subject = "Update over je aanmelding"

    message = f"""
Beste {vrijwilliger.username},

De status van je aanmelding voor de dienst:

{dienst.titel}

is gewijzigd naar:

{aanmelding.status}

Datum: {dienst.datum}
Tijd: {dienst.begin_tijd}

Met vriendelijke groet,
Vrijwilliger.nl
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [vrijwilliger.email],
        fail_silently=True,
    )

@login_required
@require_POST
def wijs_vrijwilliger_toe(request, dienst_id):
    if not heeft_rol(request.user, "projectleider"):
        return redirect("home")

    dienst = get_object_or_404(Dienst, id=dienst_id)

    user_id = request.POST.get("user_id")

    vrijwilliger = get_object_or_404(User, id=user_id)

    # check of al bestaat
    bestaande = Aanmelding.objects.filter(
        volunteer=vrijwilliger,
        dienst=dienst
    ).first()

    if bestaande:
        messages.warning(request, "Deze vrijwilliger staat al bij deze dienst.")
        return redirect("dienst_detail", dienst_id=dienst.id)

    status = "waitlist" if dienst.is_full() else "accepted"

    aanmelding = Aanmelding.objects.create(
        volunteer=vrijwilliger,
        dienst=dienst,
        status=status
    )

    # MAIL STUREN
    stuur_status_mail(aanmelding)

    if status == "waitlist":
        messages.info(request, "De dienst was al vol. De vrijwilliger is op de wachtlijst gezet.")
    else:
        messages.success(request, "Vrijwilliger succesvol toegewezen aan de dienst.")

    return redirect("dienst_detail", dienst_id=dienst.id)

@login_required
def beschikbaarheid_invullen(request):
    if get_user_role(request.user) != "vrijwilliger":
        return redirect("home")

    beschikbaarheden = list_user_availability(request.user)

    if request.method == "POST":
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            create_availability_for_user(request.user, form.cleaned_data)
            return redirect("beschikbaarheid")
    else:
        initial = {}
        if availability_has_period_fields():
            initial = {
                "valid_from": timezone.localdate(),
                "valid_until": timezone.localdate() + timedelta(days=28),
            }
        form = AvailabilityForm(initial=initial)

    return render(request, "vrijwilliger/beschikbaarheid.html", {
        "form": form,
        "beschikbaarheden": beschikbaarheden,
        "has_period_fields": availability_has_period_fields(),
    })


@login_required
@require_POST
def beschikbaarheid_verwijderen(request, beschikbaarheid_id):
    if get_user_role(request.user) != "vrijwilliger":
        return redirect("home")

    delete_availability_for_user(request.user, beschikbaarheid_id)
    return redirect("beschikbaarheid")


@login_required
def relevante_diensten(request):
    if get_user_role(request.user) != "vrijwilliger":
        return redirect("home")

    diensten = get_relevante_diensten_voor_vrijwilliger(request.user)

    return render(request, "vrijwilliger/relevante_diensten.html", {
        "diensten": diensten
    })

@login_required
def export_agenda(request):
    aanmeldingen = Aanmelding.objects.filter(
        volunteer=request.user,
        status="accepted"
    ).select_related("dienst")

    response = HttpResponse(content_type="text/calendar")
    response["Content-Disposition"] = 'attachment; filename="mijn_agenda.ics"'

    response.write("BEGIN:VCALENDAR\n")
    response.write("VERSION:2.0\n")

    for aanmelding in aanmeldingen:
        dienst = aanmelding.dienst

        start = datetime.combine(
            dienst.datum,
            dienst.begin_tijd
        ).strftime("%Y%m%dT%H%M%S")

        end = datetime.combine(
            dienst.datum,
            dienst.eind_tijd
        ).strftime("%Y%m%dT%H%M%S")

        response.write("BEGIN:VEVENT\n")
        response.write(f"SUMMARY:{dienst.titel}\n")
        response.write(f"LOCATION:{dienst.project.name}\n")
        response.write(f"DTSTART:{start}\n")
        response.write(f"DTEND:{end}\n")
        response.write("END:VEVENT\n")

    response.write("END:VCALENDAR\n")

    return response
