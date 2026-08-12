"""Génère les neuf tables de la SFD fictive de façon reproductible.

Exécution explicite uniquement : python simulation/generer.py
Même configuration et même graine donnent les mêmes fichiers CSV.
"""

import csv
import random
from datetime import date
from pathlib import Path

import yaml

from generateurs.activites import generer_activites
from generateurs.clients import generer_clients
from generateurs.credits import generer_credits
from generateurs.demandes_credit import generer_demandes
from generateurs.remboursements import generer_remboursements


RACINE = Path(__file__).resolve().parents[1]
CONFIGURATION = RACINE / "simulation" / "configuration"
SORTIE = RACINE / "donnees" / "synthetiques" / "brutes"


def lire_yaml(nom):
    return yaml.safe_load((CONFIGURATION / nom).read_text(encoding="utf-8"))


def ecrire_csv(nom, lignes):
    chemin = SORTIE / nom
    if not lignes:
        raise ValueError(f"Aucune ligne produite pour {nom}")
    with chemin.open("w", newline="", encoding="utf-8") as fichier:
        ecrivain = csv.DictWriter(fichier, fieldnames=list(lignes[0]))
        ecrivain.writeheader()
        ecrivain.writerows(lignes)


def generer_referentiels(institution, produits_configuration, aleatoire):
    agences = [
        {"identifiant_agence": f"AGC-{numero:03d}", "nom_agence": nom, "ville": nom, "date_ouverture": "2020-01-01"}
        for numero, nom in enumerate(institution["agences"], 1)
    ]
    agents = [
        {"identifiant_agent": f"AGT-{numero:03d}", "identifiant_agence": agence["identifiant_agence"], "nom_agent": f"Agent fictif {numero:02d}", "date_entree_fonction": f"202{aleatoire.randint(0, 3)}-01-01"}
        for numero, agence in enumerate((agences * 3), 1)
    ]
    produits = [
        {"identifiant_produit": f"PRD-{numero:03d}", "code_produit": produit["code"], "nom_produit": produit["nom"], "montant_min": produit["montant_min"], "montant_max": produit["montant_max"], "duree_min_mois": produit["duree_min_mois"], "duree_max_mois": produit["duree_max_mois"]}
        for numero, produit in enumerate(produits_configuration["produits"], 1)
    ]
    return agences, agents, produits


def main():
    institution = lire_yaml("institution.yaml")
    produits_configuration = lire_yaml("produits_credit.yaml")
    secteurs_configuration = lire_yaml("secteurs_activite.yaml")
    parametres = lire_yaml("simulation.yaml")
    aleatoire = random.Random(parametres["graine_aleatoire"])
    date_debut = date.fromisoformat(parametres["date_debut"])
    date_fin = date.fromisoformat(parametres["date_fin"])

    agences, agents, produits = generer_referentiels(institution, produits_configuration, aleatoire)
    clients, profils_internes = generer_clients(institution["nombre_clients"], agences, secteurs_configuration["secteurs"], date_debut, aleatoire)
    activites, resumes_activites = generer_activites(clients, profils_internes, date_debut, date_fin, aleatoire)
    demandes, metadonnees_demandes = generer_demandes(clients, profils_internes, resumes_activites, agents, produits, date_debut, date_fin, aleatoire)
    credits, echeances, metadonnees_credits = generer_credits(demandes, metadonnees_demandes)
    paiements = generer_remboursements(echeances, metadonnees_credits, aleatoire)

    SORTIE.mkdir(parents=True, exist_ok=True)
    for nom, lignes in (("agences.csv", agences), ("agents_credit.csv", agents), ("produits_credit.csv", produits), ("clients.csv", clients), ("activites.csv", activites), ("demandes_credit.csv", demandes), ("credits.csv", credits), ("echeances.csv", echeances), ("paiements.csv", paiements)):
        ecrire_csv(nom, lignes)
    print(f"SFD fictive générée avec la graine {parametres['graine_aleatoire']} : {len(clients)} clients, {len(demandes)} demandes, {len(credits)} crédits et {len(paiements)} paiements.")


if __name__ == "__main__":
    main()
