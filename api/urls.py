from django.urls import path
from .views import analyser_demande_credit, etat_service

urlpatterns = [
    path("etat/", etat_service, name="etat-service"),
    path("demandes-credit/analyser/", analyser_demande_credit, name="analyser-demande-credit"),
]
