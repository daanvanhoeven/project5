from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # --------------------
    # Basispagina's
    # --------------------
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path("profiel/", views.profiel, name="profiel"),

    # --------------------
    # Agenda
    # --------------------
    path('agenda/mijn/', views.mijn_agenda, name='mijn_agenda'),

    # --------------------
    # Contact
    # --------------------
    path('contact/', views.contactformulier, name='contactformulier'),

    # --------------------
    # Hulpaanvragen
    # --------------------
    path('hulpaanvraag/nieuw/', views.create_hulpaanvraag, name='create_hulpaanvraag'),
    path('hulpaanvraag/mijn/', views.mijn_hulpaanvragen, name='mijn_hulpaanvragen'),
    path('hulpaanvraag/<int:aanvraag_id>/', views.hulpaanvraag_detail, name='hulpaanvraag_detail'),
    path('hulpaanvraag/<int:aanvraag_id>/bewerken/', views.hulpaanvraag_update, name='hulpaanvraag_update'),
    path('hulpaanvraag/<int:aanvraag_id>/annuleren/', views.hulpaanvraag_delete, name='hulpaanvraag_delete'),

    # --------------------
    # Gebruikersbeheer (admin)
    # --------------------
    path('admin/gebruikers/', views.beheer_gebruikers, name='beheer_gebruikers'),
    path('admin/gebruikers/<int:user_id>/rol/', views.wijzig_rol, name='wijzig_rol'),

    # --------------------
    # Diensten (algemeen)
    # --------------------
    path("diensten/", views.lijst_diensten, name="lijst_diensten"),
    path("diensten/nieuw/", views.dienst_create, name="dienst_create"),  # ✅ ENIGE juiste
    path("diensten/<int:dienst_id>/", views.dienst_detail, name="dienst_detail"),
    path("diensten/<int:dienst_id>/aanmelden/", views.aanmelden_dienst, name="aanmelden_dienst"),
    path("diensten/<int:dienst_id>/afmelden/", views.afmelden_dienst, name="afmelden_dienst"),

    # --------------------
    # Admin diensten
    # --------------------
    path("admin/diensten/", views.admin_overzicht_diensten, name="admin_overzicht_diensten"),
    path("admin/diensten/<int:dienst_id>/bewerken/", views.dienst_update, name="dienst_update"),
    path("admin/diensten/<int:dienst_id>/verwijderen/", views.dienst_delete, name="dienst_delete"),

    # --------------------
    # Projectleider
    # --------------------
    path("projectleider/", views.projectleider_dashboard, name="projectleider_dashboard"),
    path("projectleider/vrijwilligers/", views.vrijwilligers_filter, name="vrijwilligers_filter"),
    path("diensten/<int:dienst_id>/toewijzen/", views.wijs_vrijwilliger_toe, name="wijs_vrijwilliger_toe"),

    # --------------------
    # Feedback
    # --------------------
    path("feedback/<int:aanvraag_id>/", views.geef_feedback, name="geef_feedback"),

    # --------------------
    # Logout
    # --------------------
    path('logout/', LogoutView.as_view(), name='logout'),
]