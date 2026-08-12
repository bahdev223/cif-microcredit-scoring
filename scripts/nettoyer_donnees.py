"""Nettoie les dossiers fictifs sans modifier la source brute.

Usage : python scripts/nettoyer_donnees.py
"""

import json
from pathlib import Path


RACINE = Path(__file__).resolve().parents[1]
SOURCE = RACINE / "donnees" / "brutes" / "dossiers_demo.json"
SORTIE = RACINE / "donnees" / "nettoyees" / "dossiers_demo_nettoyes.json"


def entier_non_negatif(dossier, champ):
    valeur = dossier[champ]
    if not isinstance(valeur, int) or valeur < 0:
        raise ValueError(f"{champ} doit être un entier positif ou nul")
    return valeur


def nettoyer(dossier):
    charges_activite = sum(
        entier_non_negatif(dossier, champ)
        for champ in ("achats_marchandises", "loyer_activite", "transport_activite", "autres_charges_activite")
    )
    depenses_menage = sum(
        entier_non_negatif(dossier, champ)
        for champ in ("alimentation", "logement", "transport_personnel", "autres_depenses_menage")
    )
    return {
        "nom_complet": dossier["nom_complet"].strip(),
        "secteur_activite": dossier["secteur_activite"].strip(),
        "objet_credit": dossier["objet_credit"].strip(),
        "montant_demande": entier_non_negatif(dossier, "montant_demande"),
        "duree_mois": entier_non_negatif(dossier, "duree_mois"),
        "chiffre_affaires": entier_non_negatif(dossier, "chiffre_affaires"),
        "charges_activite": charges_activite,
        "depenses_menage": depenses_menage,
        "mensualite_dette_existante": entier_non_negatif(dossier, "mensualite_dette_existante"),
        "anciennete_activite_mois": entier_non_negatif(dossier, "anciennete_activite_mois"),
        "nombre_retards": entier_non_negatif(dossier, "nombre_retards"),
        "regularite_tontine": dossier["regularite_tontine"],
        "credits_termines": entier_non_negatif(dossier, "credits_termines"),
    }


if __name__ == "__main__":
    dossiers = json.loads(SOURCE.read_text(encoding="utf-8"))
    SORTIE.write_text(json.dumps([nettoyer(dossier) for dossier in dossiers], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(dossiers)} dossiers nettoyés : {SORTIE}")
