from django.urls import path
from .views import (
    analyser_demande_credit,
    creer_client,
    enregistrer_institution,
    etat_service,
    lire_institution,
    liste_clients,
    liste_demandes_credit,
)

urlpatterns = [
    path("etat/", etat_service, name="etat-service"),
    path("institution/", lire_institution, name="lire-institution"),
    path("institution/enregistrer/", enregistrer_institution, name="enregistrer-institution"),
    path("clients/", liste_clients, name="liste-clients"),
    path("clients/creer/", creer_client, name="creer-client"),
    path("demandes-credit/", liste_demandes_credit, name="liste-demandes-credit"),
    path("demandes-credit/analyser/", analyser_demande_credit, name="analyser-demande-credit"),
]
