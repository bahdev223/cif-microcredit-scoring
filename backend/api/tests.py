from django.test import TestCase

from clients.models import Client
from credits.models import CreditImporte, PaiementImporte


class ApiMetierTests(TestCase):
    def setUp(self):
        self.client_metier = Client.objects.create(
            nom_complet="Client test", secteur_activite="Commerce",
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
        for chemin in ("/api/clients/", "/api/portefeuille/", "/api/retards/", "/api/audit/"):
            self.assertEqual(self.client.get(chemin).status_code, 200)

    def test_listes_transactionnelles_retirees(self):
        """Les listes plates de crédits et de versements ont été retirées.

        Elles n'apportaient aucune lecture analytique : le portefeuille porte
        les crédits avec leur statut, et le dossier client porte les versements
        échéance par échéance.
        """
        for chemin in ("/api/credits/", "/api/remboursements/", "/api/regles-analyse/"):
            self.assertEqual(self.client.get(chemin).status_code, 404)

    def test_detail_client(self):
        reponse = self.client.get(f"/api/clients/{self.client_metier.id}/")
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.json()["client"]["nom_complet"], "Client test")

