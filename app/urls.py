from django.urls import path, include
from django.contrib import admin
from . import views
from .views import CustomLoginView

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),  # voor logout/reset
    path('register/', views.register, name='register'),
    path('agenda/mijn/', views.mijn_agenda, name='mijn_agenda'),
    path('contactformulier/', views.contactformulier, name='contactformulier'),
]
