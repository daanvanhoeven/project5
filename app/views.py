from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Agenda
from .forms import ContactForm
from .models import ContactBericht
from django.contrib.auth.views import LoginView

# Create your views here.
def home(request):
    return render(request, "home.html")

#def contactformulier(request):
    #return render(request, 'contactformulier.html')

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()   # sla gebruiker op in database
            login(request, user) # log meteen in na registratie
            return redirect("home")  # stuur door naar homepage
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
            form.save()  # sla bericht op in database
            return redirect("contactformulier")  # of naar een bedankpagina
    else:
        form = ContactForm()
    return render(request, "contactformulier.html", {"form": form})

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        user = self.request.user

        # Admins direct naar admin
        if user.is_superuser or user.is_staff:
            return '/admin/'

        # Als er een 'next' parameter is → gebruik die
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url

        # Anders naar agenda
        return '/agenda/mijn/'


