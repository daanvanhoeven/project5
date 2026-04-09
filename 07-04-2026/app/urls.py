from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin/gebruikers/', views.beheer_gebruikers, name='beheer_gebruikers'),
    path('admin/gebruikers/<int:user_id>/rol/', views.wijzig_rol, name='wijzig_rol'),

    path('agenda/mijn/', views.mijn_agenda, name='mijn_agenda'),
    path("profiel/", views.profiel, name="profiel"),

    path('hulpaanvraag/nieuw/', views.create_hulpaanvraag, name='create_hulpaanvraag'),
    path('hulpaanvraag/mijn/', views.mijn_hulpaanvragen, name='mijn_hulpaanvragen'),
    path('hulpaanvraag/<int:aanvraag_id>/', views.hulpaanvraag_detail, name='hulpaanvraag_detail'),
    path('contact/', views.contactformulier, name='contactformulier'),
    path("diensten/", views.lijst_diensten, name="lijst_diensten"),


]
