from django.urls import path, include
from . import views
from .views import CustomLoginView

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', views.register, name='register'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('agenda/mijn/', views.mijn_agenda, name='mijn_agenda'),
    path('contactformulier/', views.contactformulier, name='contactformulier'),

    # ADMIN FUNCTIES (JE EIGEN DASHBOARD)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin/gebruikers/', views.beheer_gebruikers, name='beheer_gebruikers'),
    path('admin/gebruikers/<int:user_id>/rol/', views.wijzig_rol, name='wijzig_rol'),
    # Diensten & Aanmeldingen
    path('diensten/', views.lijst_diensten, name='lijst_diensten'),
    path('diensten/<int:dienst_id>/', views.dienst_detail, name='dienst_detail'),
    path('diensten/<int:dienst_id>/aanmelden/', views.aanmeld_dienst, name='aanmeld_dienst'),
    # Hulpaanvragen
    path('hulpaanvraag/nieuw/', views.create_hulpaanvraag, name='create_hulpaanvraag'),
    path('hulpaanvraag/mijn/', views.mijn_hulpaanvragen, name='mijn_hulpaanvragen'),
    path('hulpaanvraag/<int:aanvraag_id>/', views.hulpaanvraag_detail, name='hulpaanvraag_detail'),
    
]
