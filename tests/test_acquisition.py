"""Contrôles de la couche d'acquisition.

Le scénario de référence est celui d'une institution qui exporte ses données
avec ses propres noms de colonnes, son propre séparateur et son propre
encodage. La plateforme doit reconnaître ce qu'elle peut, dire ce qu'elle ne
reconnaît pas, et ne jamais décider seule.

    python tests/test_acquisition.py
"""

import io
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from acquisition.correspondance import (  # noqa: E402
    appliquer, normaliser, proposer_champ, proposer_correspondance, proposer_table,
)
from acquisition.lecture import LectureImpossible, lire  # noqa: E402

reussis, echoues = 0, 0


def verifier(intitule, condition):
    global reussis, echoues
    if condition:
        reussis += 1
        print(f"  ok     {intitule}")
    else:
        echoues += 1
        print(f"  ECHEC  {intitule}")


def fichier(nom, contenu, encodage="utf-8"):
    flux = io.BytesIO(contenu.encode(encodage))
    flux.name = nom
    return flux


# ---------- Lecture ----------

print("\nLECTURE DES FICHIERS")

entetes, lignes = lire(fichier("export.csv", "CLIENT;NOM;CA_MENSUEL\nCLT-1;Fatou;700000\nCLT-2;Bakary;250000\n"))
verifier("séparateur point-virgule détecté", entetes == ["CLIENT", "NOM", "CA_MENSUEL"])
verifier("lignes lues", len(lignes) == 2 and lignes[0]["NOM"] == "Fatou")

entetes, _ = lire(fichier("export.csv", "CLIENT\tNOM\tCA\nCLT-1\tFatou\t700000\n"))
verifier("séparateur tabulation détecté", entetes == ["CLIENT", "NOM", "CA"])

_, lignes = lire(fichier("export.csv", "CLIENT;NOM\nCLT-1;Aminata Traoré\n", encodage="cp1252"))
verifier("encodage windows accepté", lignes[0]["NOM"] == "Aminata Traoré")

entetes, lignes = lire(fichier("export.csv",
    "Export du 12/08/2026\n\nCLIENT;MONTANT\nCLT-1;500000\n"))
verifier("ligne de titre ignorée", entetes == ["CLIENT", "MONTANT"])
verifier("données lues sous le vrai en-tête", lignes[0]["MONTANT"] == "500000")

entetes, _ = lire(fichier("export.csv", "CLIENT;;MONTANT\nCLT-1;x;500000\n"))
verifier("colonne sans nom renommée", entetes[1].startswith("colonne_"))

entetes, _ = lire(fichier("export.csv", "MONTANT;MONTANT\n1;2\n"))
verifier("colonnes homonymes distinguées", entetes == ["MONTANT", "MONTANT_2"])

try:
    lire(fichier("vide.csv", ""))
    verifier("fichier vide refusé", False)
except LectureImpossible:
    verifier("fichier vide refusé", True)

try:
    lire(fichier("entete_seule.csv", "CLIENT;MONTANT\n"))
    verifier("fichier sans données refusé", False)
except LectureImpossible:
    verifier("fichier sans données refusé", True)

# Excel : une institution exporte plus souvent en tableur qu'en CSV.
from openpyxl import Workbook  # noqa: E402

classeur = Workbook()
feuille = classeur.active
feuille.append(["MATRICULE", "NOM", "MONTANT_OCTROYE", "DATE_DEBLOCAGE"])
feuille.append(["CLT-1", "Fatou", 500000, "2024-03-10"])
feuille.append(["CLT-2", "Bakary", 250000, "2024-05-02"])
flux_excel = io.BytesIO()
classeur.save(flux_excel)
flux_excel.seek(0)
flux_excel.name = "prets.xlsx"

entetes, lignes = lire(flux_excel)
verifier("classeur Excel lu", entetes == ["MATRICULE", "NOM", "MONTANT_OCTROYE", "DATE_DEBLOCAGE"])
verifier("nombres du tableur ramenés en texte", lignes[0]["MONTANT_OCTROYE"] == "500000")
verifier("deux lignes lues depuis Excel", len(lignes) == 2 and lignes[1]["NOM"] == "Bakary")

# ---------- Normalisation ----------

print("\nNORMALISATION DES ÉCRITURES")
verifier("accents retirés", normaliser("Montant Décaissé") == "montant_decaisse")
verifier("ponctuation ramenée", normaliser("montant.decaisse") == "montant_decaisse")
verifier("majuscules ramenées", normaliser("MONTANT_DECAISSE") == "montant_decaisse")
verifier("espaces multiples réduits", normaliser("  Date   d'échéance ") == "date_d_echeance")

# ---------- Correspondance des colonnes ----------

print("\nCORRESPONDANCE DES COLONNES")
proposition = proposer_champ("MONTANT_OCTROYE", "credits")
verifier("synonyme reconnu", proposition["champ"] == "montant_decaisse" and proposition["certitude"] == "certaine")

proposition = proposer_champ("identifiant_credit", "credits")
verifier("code identique reconnu", proposition["champ"] == "identifiant_credit")

proposition = proposer_champ("DT_ECHEANCE", "echeances")
verifier("abréviation reconnue", proposition["champ"] == "date_exigible")

proposition = proposer_champ("montant_du_", "echeances")
verifier("écriture proche acceptée", proposition["champ"] == "montant_du")

proposition = proposer_champ("REVENU_EPOUX", "clients")
verifier("colonne inconnue signalée", proposition["champ"] == "" and proposition["certitude"] == "inconnue")

proposition = proposer_champ("MATRICULE", "credits", deja_pris={"identifiant_client"})
verifier("champ déjà associé non proposé deux fois", proposition["champ"] != "identifiant_client")

# ---------- Détection de la table ----------

print("\nDÉTECTION DE LA TABLE")
verifier("table devinée par les colonnes seules",
         proposer_table("export_2026.csv", ["ID_PRET", "DEMANDE", "MONTANT_OCTROYE", "DATE_OCTROI"])["table"] == "credits")
verifier("table devinée par le nom du fichier",
         proposer_table("paiements.csv", ["A", "B"])["table"] == "paiements")
verifier("fichier hors sujet non rattaché",
         proposer_table("stock_boutique.csv", ["ARTICLE", "QUANTITE", "PRIX_UNITAIRE"])["table"] == "")

# ---------- Le cas d'un export réel ----------

print("\nUN EXPORT AVEC LES NOMS DE L'INSTITUTION")
entetes, lignes = lire(fichier("PRETS_2026.csv",
    "NUM_CREDIT;NUMERO_DOSSIER;MATRICULE;MONTANT_OCTROYE;NB_MOIS;DATE_DEBLOCAGE;AGENT_SUIVI\n"
    "CR-001;DOS-001;CLT-1;500000;12;2024-03-10;Awa\n"
    "CR-002;DOS-002;CLT-2;250000;6;2024-05-02;Moussa\n"))
correspondance = proposer_correspondance("PRETS_2026.csv", entetes)

verifier("table identifiée", correspondance["table"] == "credits")
associations = {colonne["colonne"]: colonne["champ"] for colonne in correspondance["colonnes"]}
verifier("NUM_CREDIT associé", associations["NUM_CREDIT"] == "identifiant_credit")
verifier("NUMERO_DOSSIER associé", associations["NUMERO_DOSSIER"] == "identifiant_demande")
verifier("MATRICULE associé", associations["MATRICULE"] == "identifiant_client")
verifier("MONTANT_OCTROYE associé", associations["MONTANT_OCTROYE"] == "montant_decaisse")
verifier("NB_MOIS associé", associations["NB_MOIS"] == "duree_mois")
verifier("DATE_DEBLOCAGE associé", associations["DATE_DEBLOCAGE"] == "date_decaissement")
verifier("AGENT_SUIVI laissé non reconnu", associations["AGENT_SUIVI"] == "")
verifier("colonne non reconnue listée", correspondance["colonnes_non_reconnues"] == ["AGENT_SUIVI"])

normalisees, ecartees = appliquer(correspondance, lignes)
verifier("ligne traduite vers le référentiel", normalisees[0]["montant_decaisse"] == "500000")
verifier("identifiants traduits", normalisees[1]["identifiant_credit"] == "CR-002")
verifier("colonne non associée conservée à part", ecartees[0]["AGENT_SUIVI"] == "Awa")
verifier("colonne non associée absente du référentiel", "AGENT_SUIVI" not in normalisees[0])

# ---------- Champs obligatoires manquants ----------

print("\nCHAMPS ATTENDUS ET ABSENTS")
entetes, _ = lire(fichier("echeances.csv", "ID_ECHEANCE;DATE_ECHEANCE;MONTANT\nE1;2024-04-10;41667\n"))
correspondance = proposer_correspondance("echeances.csv", entetes)
manquants_obligatoires = [champ["champ"] for champ in correspondance["champs_non_associes"] if champ["obligatoire"]]
verifier("champ obligatoire absent signalé", "identifiant_credit" in manquants_obligatoires)
verifier("champ facultatif absent signalé sans alarme",
         any(champ["champ"] == "numero" and not champ["obligatoire"]
             for champ in correspondance["champs_non_associes"]))

print(f"\n{reussis}/{reussis + echoues} contrôles passés.")
sys.exit(1 if echoues else 0)
