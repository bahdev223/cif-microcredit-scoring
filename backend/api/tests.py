from django.test import TestCase

from clients.models import Client
from credits.models import CreditImporte, PaiementImporte


class ApiMetierTests(TestCase):
    def setUp(self):
        self.client_metier = Client.objects.create(
            nom_complet="Client test", secteur_activite="Commerce",
            revenu_mensuel=100000, charges_mensuelles=30000,
            anciennete_activite_mois=24,
        )
        credit = CreditImporte.objects.create(
            client=self.client_metier, identifiant_source="CRD-TEST",
            montant_decaisse=120000, duree_mois=12,
        )
        PaiementImporte.objects.create(
            credit=credit, identifiant_source="PAI-TEST", montant_paye=10000,
        )

    def test_tableau_bord(self):
        reponse = self.client.get("/api/tableau-bord/")
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.json()["credits"], 1)

    def test_listes_metier(self):
        for chemin in ("/api/clients/", "/api/credits/", "/api/remboursements/", "/api/audit/"):
            self.assertEqual(self.client.get(chemin).status_code, 200)

    def test_detail_client(self):
        reponse = self.client.get(f"/api/clients/{self.client_metier.id}/")
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.json()["client"]["nom_complet"], "Client test")

