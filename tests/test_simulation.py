import csv
import hashlib
import subprocess
import sys
from pathlib import Path


RACINE = Path(__file__).resolve().parents[1]
BRUTES = RACINE / "donnees" / "synthetiques" / "brutes"
TABLES = {"agences.csv", "agents_credit.csv", "produits_credit.csv", "clients.csv", "activites.csv", "demandes_credit.csv", "credits.csv", "echeances.csv", "paiements.csv"}


def empreintes():
    return {nom: hashlib.sha256((BRUTES / nom).read_bytes()).hexdigest() for nom in TABLES}


def test_simulation_reproductible_et_relations_coherentes():
    commande = [sys.executable, str(RACINE / "simulation" / "generer.py")]
    subprocess.run(commande, check=True, cwd=RACINE)
    premiere = empreintes()
    subprocess.run(commande, check=True, cwd=RACINE)
    assert premiere == empreintes()

    def lire(nom):
        with (BRUTES / nom).open(encoding="utf-8", newline="") as fichier:
            return list(csv.DictReader(fichier))

    agences = {ligne["identifiant_agence"] for ligne in lire("agences.csv")}
    clients = {ligne["identifiant_client"] for ligne in lire("clients.csv")}
    agents = {ligne["identifiant_agent"] for ligne in lire("agents_credit.csv")}
    produits = {ligne["identifiant_produit"] for ligne in lire("produits_credit.csv")}
    demandes = {ligne["identifiant_demande"]: ligne for ligne in lire("demandes_credit.csv")}
    credits = {ligne["identifiant_credit"] for ligne in lire("credits.csv")}
    echeances = {ligne["identifiant_echeance"] for ligne in lire("echeances.csv")}
    assert all(ligne["identifiant_agence"] in agences for ligne in lire("clients.csv"))
    assert all(ligne["identifiant_client"] in clients and ligne["identifiant_agent"] in agents and ligne["identifiant_produit"] in produits for ligne in demandes.values())
    assert all(demandes[ligne["identifiant_demande"]]["statut"] == "ACCEPTEE" for ligne in lire("credits.csv"))
    assert all(ligne["identifiant_credit"] in credits for ligne in lire("echeances.csv"))
    assert all(ligne["identifiant_echeance"] in echeances for ligne in lire("paiements.csv"))
