import json
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
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

    def test_ecran_import_excel_est_rendu(self):
        reponse = self.client.get("/")
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Analyser un export institutionnel")
        self.assertContains(reponse, 'id="lot-acquisition"')

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

    def test_analyse_et_controle_d_un_export_excel(self):
        """L'export est seulement lu et contrôlé : aucune écriture métier n'est faite."""
        from openpyxl import Workbook

        classeur = Workbook()
        classeur.active.title = "Page de garde"
        classeur.active.append(["Export mensuel"])
        feuille = classeur.create_sheet("Historique crédits")
        feuille.append(["NUM_CREDIT", "NUM_DEMANDE", "NUM_SOC", "MT_PRET", "DT_DECAIS"])
        feuille.append(["CR-01", "DM-01", "CL-01", 300000, "2026-01-12"])
        flux = BytesIO()
        classeur.save(flux)
        contenu = flux.getvalue()

        reponse = self.client.post("/api/acquisition/analyser-fichier/", {
            "fichier": SimpleUploadedFile("historique.xlsx", contenu),
            "feuille": "Historique crédits",
        })
        self.assertEqual(reponse.status_code, 200)
        resultat = reponse.json()
        self.assertIn("Historique crédits", resultat["feuilles"])
        self.assertEqual(resultat["correspondance"]["table"], "credits")

        reponse = self.client.post("/api/acquisition/valider-correspondance/", {
            "fichier": SimpleUploadedFile("historique.xlsx", contenu),
            "feuille": "Historique crédits",
            "correspondance": json.dumps(resultat["correspondance"]),
        })
        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(reponse.json()["rapport"]["integrable"])
        self.assertFalse(reponse.json()["persiste"])

    def test_lot_mappe_est_controle_puis_persiste(self):
        """Les relations entre exports sont contrôlées avant toute écriture."""
        sources = {
            "clients": ("clients.csv", "identifiant_client;nom_client;code_secteur_principal\nCL-LOT;Awa Koné;commerce\n"),
            "demandes_credit": ("demandes.csv", "identifiant_demande;identifiant_client;montant_demande\nDM-LOT;CL-LOT;200000\n"),
            "credits": ("credits.csv", "identifiant_credit;identifiant_demande;montant_decaisse\nCR-LOT;DM-LOT;200000\n"),
            "echeances": ("echeances.csv", "identifiant_echeance;identifiant_credit;montant_du\nEC-LOT;CR-LOT;25000\n"),
            "paiements": ("paiements.csv", "identifiant_paiement;identifiant_credit;montant_paye\nPA-LOT;CR-LOT;25000\n"),
        }
        correspondances = []
        fichiers = []
        for table, (nom, contenu) in sources.items():
            entetes = contenu.splitlines()[0].split(";")
            correspondances.append({"table": table, "colonnes": [{"colonne": entete, "champ": entete} for entete in entetes]})
            fichiers.append(SimpleUploadedFile(nom, contenu.encode(), content_type="text/csv"))

        donnees = {"fichiers": fichiers, "correspondances": json.dumps(correspondances)}
        reponse = self.client.post("/api/acquisition/valider-lot/", donnees)
        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(reponse.json()["rapport"]["integrable"])
        self.assertFalse(reponse.json()["persiste"])

        fichiers = [SimpleUploadedFile(nom, contenu.encode(), content_type="text/csv") for nom, contenu in sources.values()]
        reponse = self.client.post("/api/acquisition/confirmer-lot/", {"fichiers": fichiers, "correspondances": json.dumps(correspondances)})
        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(reponse.json()["persiste"])
        client = Client.objects.get(identifiant_source="CL-LOT")
        self.assertTrue(CreditImporte.objects.filter(identifiant_source="CR-LOT").exists())
        dossier = self.client.get(f"/api/clients/{client.id}/").json()
        self.assertEqual(len(dossier["historique_credit"]), 1)
        self.assertEqual(dossier["historique_credit"][0]["identifiant"], "CR-LOT")

