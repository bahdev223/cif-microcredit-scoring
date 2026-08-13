from django.urls import path
from .views import (
    analyser_demande_credit,
    creer_client,
    detail_client,
    enregistrer_institution,
    etat_service,
    lire_institution,
    liste_lots_import,
    liste_clients,
    liste_demandes_credit,
    valider_import_csv,
    confirmer_import_csv,
)

urlpatterns = [
    path("etat/", etat_service, name="etat-service"),
    path("institution/", lire_institution, name="lire-institution"),
    path("institution/enregistrer/", enregistrer_institution, name="enregistrer-institution"),
    path("clients/", liste_clients, name="liste-clients"),
    path("clients/creer/", creer_client, name="creer-client"),
    path("clients/<int:identifiant_client>/", detail_client, name="detail-client"),
    path("demandes-credit/", liste_demandes_credit, name="liste-demandes-credit"),
    path("imports-csv/valider/", valider_import_csv, name="valider-import-csv"),
    path("imports-csv/lots/", liste_lots_import, name="liste-lots-import"),
    path("imports-csv/confirmer/", confirmer_import_csv, name="confirmer-import-csv"),
    path("demandes-credit/analyser/", analyser_demande_credit, name="analyser-demande-credit"),
]
