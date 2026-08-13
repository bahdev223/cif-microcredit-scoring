"""Compare les cinq mondes produits par le simulateur.

La question posée au laboratoire est : est-ce qu'un même moteur de scoring
s'adapte à des environnements différents ? Encore faut-il que ces
environnements soient réellement différents. Ce script mesure les écarts entre
institutions sur ce qui compte pour un modèle : la population, l'octroi, le
risque, la saisonnalité et la qualité des données.

    python simulation/comparer_mondes.py
"""

import csv
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date
import os
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
REPERTOIRE_DONNEES = Path(os.environ.get(
    "CIF_REPERTOIRE_DONNEES",
    RACINE.parent / "cif-microcredit-donnees-locales" / "synthetiques",
))
BRUTES = REPERTOIRE_DONNEES / "brutes"
TRAITEES = REPERTOIRE_DONNEES / "traitees"
VERITE = REPERTOIRE_DONNEES / "verite"

FIN_DU_MONDE = date(2025, 12, 31)


def lire(dossier, nom):
    with (dossier / nom).open(encoding="utf-8") as fichier:
        return list(csv.DictReader(fichier))


def par_institution(lignes):
    groupes = defaultdict(list)
    for ligne in lignes:
        groupes[ligne["identifiant_institution"]].append(ligne)
    return groupes


def afficher(titre, mesures, institutions, format_valeur="{:.1f}"):
    ligne = f"  {titre:<34}"
    for identifiant in institutions:
        valeur = mesures.get(identifiant)
        texte = "-" if valeur is None else format_valeur.format(valeur)
        ligne += f"{texte:>13}"
    print(ligne)


def main():
    institutions = [ligne["identifiant_institution"] for ligne in lire(BRUTES, "01_institutions.csv")]
    profils = {ligne["identifiant_institution"]: ligne for ligne in lire(VERITE, "01_profils_institutions.csv")}
    clients = par_institution(lire(BRUTES, "06_clients.csv"))
    demandes_brutes = lire(BRUTES, "09_demandes_credit.csv")
    demandes = par_institution(demandes_brutes)
    decisions = par_institution(lire(BRUTES, "10_decisions_credit.csv"))
    credits = par_institution(lire(BRUTES, "11_credits.csv"))
    resultats = par_institution(lire(TRAITEES, "14_resultats_credit.csv"))
    releves = par_institution(lire(BRUTES, "07b_releves_activite.csv"))

    print("Comparaison des cinq mondes synthétiques\n")
    entete = f"  {'':<34}"
    for identifiant in institutions:
        entete += f"{identifiant:>13}"
    print(entete)
    print("  " + "-" * (34 + 13 * len(institutions)))

    print("\n  POPULATION")
    afficher("clients", {i: len(clients[i]) for i in institutions}, institutions, "{:.0f}")
    anciennete = {}
    part_recents = {}
    for identifiant in institutions:
        mois = [
            (FIN_DU_MONDE - date.fromisoformat(ligne["date_entree_relation"])).days / 30.4
            for ligne in clients[identifiant]
        ]
        anciennete[identifiant] = statistics.median(mois) if mois else None
        part_recents[identifiant] = 100 * sum(1 for valeur in mois if valeur < 12) / len(mois) if mois else None
    afficher("ancienneté médiane (mois)", anciennete, institutions)
    afficher("part entrés depuis moins d'un an (%)", part_recents, institutions)

    secteur_dominant = {}
    for identifiant in institutions:
        compte = Counter(ligne["code_secteur_principal"] for ligne in clients[identifiant])
        code, nombre = compte.most_common(1)[0]
        secteur_dominant[identifiant] = f"{code[:11]} {100 * nombre / len(clients[identifiant]):.0f}%"
    ligne = f"  {'secteur dominant':<34}"
    for identifiant in institutions:
        ligne += f"{secteur_dominant[identifiant]:>13}"
    print(ligne)

    print("\n  OCTROI")
    afficher("demandes par client",
             {i: len(demandes[i]) / len(clients[i]) for i in institutions}, institutions, "{:.2f}")
    taux_acceptation, taux_cible = {}, {}
    for identifiant in institutions:
        lignes = decisions[identifiant]
        taux_acceptation[identifiant] = 100 * sum(1 for l in lignes if l["statut"] == "ACCEPTEE") / len(lignes)
        taux_cible[identifiant] = 100 * float(profils[identifiant]["taux_acceptation_cible"])
    afficher("taux d'acceptation (%)", taux_acceptation, institutions)
    afficher("  cible", taux_cible, institutions)
    afficher("montant médian décaissé (F)",
             {i: statistics.median([int(l["montant_decaisse"]) for l in credits[i]]) for i in institutions},
             institutions, "{:.0f}")
    afficher("durée médiane (mois)",
             {i: statistics.median([int(l["duree_mois"]) for l in credits[i]]) for i in institutions},
             institutions, "{:.0f}")

    print("\n  RISQUE")
    taux_defaut, cible_defaut, retard, censure = {}, {}, {}, {}
    for identifiant in institutions:
        lignes = resultats[identifiant]
        observables = [l for l in lignes if l["observation_censuree"] == "0"]
        taux_defaut[identifiant] = 100 * sum(1 for l in observables if l["defaut_experimental"] == "1") / len(observables) if observables else None
        cible_defaut[identifiant] = 100 * float(profils[identifiant]["taux_defaut_experimental_cible"])
        retard[identifiant] = statistics.mean([int(l["jours_retard_max"]) for l in observables]) if observables else None
        censure[identifiant] = 100 * (1 - len(observables) / len(lignes)) if lignes else None
    afficher("taux de défaut observé (%)", taux_defaut, institutions)
    afficher("  cible", cible_defaut, institutions)
    afficher("retard maximal moyen (jours)", retard, institutions)
    afficher("observations censurées (%)", censure, institutions)

    print("\n  QUALITÉ DES DONNÉES")
    manquantes, facteur = {}, {}
    for identifiant in institutions:
        lignes = releves[identifiant]
        cellules = len(lignes) * 5
        vides = sum(
            1 for ligne in lignes
            for colonne in ("recettes_mensuelles_declarees", "charges_mensuelles_declarees",
                            "stock_estime", "autres_revenus_menage", "charges_menage")
            if ligne[colonne] == ""
        )
        manquantes[identifiant] = 100 * vides / cellules if cellules else None
        facteur[identifiant] = float(profils[identifiant]["facteur_qualite_donnees"])
    afficher("cellules manquantes dans les relevés (%)", manquantes, institutions)
    afficher("  facteur qualité de l'institution", facteur, institutions, "{:.2f}")

    print("\n  SAISONNALITÉ ET CHOC MACRO (vérité)")
    recettes_par_mois = defaultdict(lambda: defaultdict(list))
    with (VERITE / "08_situations_mensuelles.csv").open(encoding="utf-8") as fichier:
        for ligne in csv.DictReader(fichier):
            recettes_par_mois[ligne["identifiant_institution"]][ligne["mois"]].append(int(ligne["recettes_reelles"]))

    amplitude, choc = {}, {}
    for identifiant in institutions:
        moyennes = {mois: statistics.mean(valeurs) for mois, valeurs in recettes_par_mois[identifiant].items()}
        if not moyennes:
            continue
        par_mois_calendaire = defaultdict(list)
        for mois, valeur in moyennes.items():
            par_mois_calendaire[mois[5:]].append(valeur)
        profil_mensuel = [statistics.mean(valeurs) for _, valeurs in sorted(par_mois_calendaire.items())]
        moyenne = statistics.mean(profil_mensuel)
        amplitude[identifiant] = 100 * (max(profil_mensuel) - min(profil_mensuel)) / moyenne

        # Le choc court de juin à décembre 2023 : on le compare aux mêmes mois
        # de 2022 et 2024, jamais au premier semestre. Sinon la récolte, qui
        # tombe précisément dans cette fenêtre, masquerait entièrement la chute.
        pendant = [valeur for mois, valeur in moyennes.items() if "2023-06" <= mois <= "2023-12"]
        reference = [
            valeur for mois, valeur in moyennes.items()
            if "2022-06" <= mois <= "2022-12" or "2024-06" <= mois <= "2024-12"
        ]
        choc[identifiant] = 100 * (statistics.mean(pendant) / statistics.mean(reference) - 1) if pendant and reference else None
    afficher("amplitude saisonnière des recettes (%)", amplitude, institutions)
    afficher("effet du choc 2023 sur les recettes (%)", choc, institutions, "{:+.1f}")
    afficher("  sensibilité macro de l'institution",
             {i: float(profils[i]["sensibilite_macro"]) for i in institutions}, institutions, "{:.2f}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
