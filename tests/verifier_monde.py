"""Contrôle de cohérence du monde synthétique.

Ce script est la spécification exécutable du dictionnaire : il vérifie les
invariants du paragraphe 14 de documentation/07-dictionnaire-donnees-synthetiques.md.
Un monde qui échoue ici ne doit pas être publié.

    python tests/verifier_monde.py
"""

import csv
import sys
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

DEBUT_DU_MONDE = date(2021, 1, 1)
FIN_DU_MONDE = date(2025, 12, 31)

controles = []


def lire(dossier, nom):
    with (dossier / nom).open(encoding="utf-8") as fichier:
        return list(csv.DictReader(fichier))


def verifier(intitule, condition, detail=""):
    controles.append((intitule, bool(condition), detail))


def jour(valeur):
    return date.fromisoformat(valeur)


def main():
    institutions = lire(BRUTES, "01_institutions.csv")
    agences = lire(BRUTES, "02_agences.csv")
    agents = lire(BRUTES, "03_agents_credit.csv")
    produits = lire(BRUTES, "04_produits_credit.csv")
    secteurs = lire(BRUTES, "05_secteurs_activite.csv")
    clients = lire(BRUTES, "06_clients.csv")
    activites = lire(BRUTES, "07_activites.csv")
    releves = lire(BRUTES, "07b_releves_activite.csv")
    demandes = lire(BRUTES, "09_demandes_credit.csv")
    decisions = lire(BRUTES, "10_decisions_credit.csv")
    credits = lire(BRUTES, "11_credits.csv")
    echeances = lire(BRUTES, "12_echeances.csv")
    paiements = lire(BRUTES, "13_paiements.csv")
    resultats = lire(TRAITEES, "14_resultats_credit.csv")
    mix_sectoriel = lire(VERITE, "01_mix_sectoriel.csv")
    mix_produits = lire(VERITE, "01_mix_produits.csv")
    profils_latents = lire(VERITE, "06_profils_latents.csv")

    identifiants = {
        "institution": {ligne["identifiant_institution"] for ligne in institutions},
        "agence": {ligne["identifiant_agence"] for ligne in agences},
        "agent": {ligne["identifiant_agent"] for ligne in agents},
        "produit": {ligne["identifiant_produit"] for ligne in produits},
        "secteur": {ligne["code_secteur"] for ligne in secteurs},
        "client": {ligne["identifiant_client"] for ligne in clients},
        "activite": {ligne["identifiant_activite"] for ligne in activites},
        "releve": {ligne["identifiant_releve"] for ligne in releves},
        "demande": {ligne["identifiant_demande"] for ligne in demandes},
        "credit": {ligne["identifiant_credit"] for ligne in credits},
        "echeance": {ligne["identifiant_echeance"] for ligne in echeances},
    }

    # 1 — intégrité référentielle
    verifier("clés primaires uniques (clients)", len(identifiants["client"]) == len(clients))
    verifier("clés primaires uniques (relevés)", len(identifiants["releve"]) == len(releves))
    verifier("clés primaires uniques (paiements)",
             len({ligne["identifiant_paiement"] for ligne in paiements}) == len(paiements))
    verifier("agences rattachées à une institution connue",
             all(ligne["identifiant_institution"] in identifiants["institution"] for ligne in agences))
    verifier("clients rattachés à une agence connue",
             all(ligne["identifiant_agence"] in identifiants["agence"] for ligne in clients))
    verifier("activités rattachées à un client connu",
             all(ligne["identifiant_client"] in identifiants["client"] for ligne in activites))
    verifier("relevés rattachés à une activité connue",
             all(ligne["identifiant_activite"] in identifiants["activite"] for ligne in releves))
    verifier("demandes rattachées à un client, un agent et un produit connus",
             all(ligne["identifiant_client"] in identifiants["client"]
                 and ligne["identifiant_agent"] in identifiants["agent"]
                 and ligne["identifiant_produit"] in identifiants["produit"] for ligne in demandes))
    verifier("échéances rattachées à un crédit connu",
             all(ligne["identifiant_credit"] in identifiants["credit"] for ligne in echeances))
    verifier("paiements rattachés à un crédit connu",
             all(ligne["identifiant_credit"] in identifiants["credit"] for ligne in paiements))
    verifier("paiements rattachés à une échéance connue quand ils le sont",
             all(not ligne["identifiant_echeance"] or ligne["identifiant_echeance"] in identifiants["echeance"]
                 for ligne in paiements))
    verifier("secteurs des clients connus",
             all(ligne["code_secteur_principal"] in identifiants["secteur"] for ligne in clients))

    # 2 — cohérence de l'institution le long de la chaîne
    institution_par_agence = {ligne["identifiant_agence"]: ligne["identifiant_institution"] for ligne in agences}
    institution_par_client = {ligne["identifiant_client"]: ligne["identifiant_institution"] for ligne in clients}
    verifier("le client et son agence appartiennent à la même institution",
             all(institution_par_agence[ligne["identifiant_agence"]] == ligne["identifiant_institution"]
                 for ligne in clients))
    verifier("la demande et son client appartiennent à la même institution",
             all(institution_par_client[ligne["identifiant_client"]] == ligne["identifiant_institution"]
                 for ligne in demandes))

    # 3 et 4 — cohérence des référentiels d'institution
    for nom, table, colonne in (("sectoriel", mix_sectoriel, "poids_population"),
                                ("produits", mix_produits, "poids_octroi")):
        sommes = {}
        for ligne in table:
            sommes[ligne["identifiant_institution"]] = sommes.get(ligne["identifiant_institution"], 0.0) + float(ligne[colonne])
        verifier(f"le mix {nom} somme à 1 par institution",
                 all(abs(valeur - 1.0) < 1e-6 for valeur in sommes.values()),
                 str({cle: round(valeur, 4) for cle, valeur in sommes.items()}))

    verifier("les codes secteurs des mix existent dans le référentiel",
             all(ligne["code_secteur"] in identifiants["secteur"] for ligne in mix_sectoriel))
    codes_produits = {ligne["code_produit"] for ligne in produits}
    verifier("les codes produits des mix existent dans le référentiel",
             all(ligne["code_produit"] in codes_produits for ligne in mix_produits))

    # 6 — une décision par demande, un crédit par acceptation
    demandes_decidees = [ligne["identifiant_demande"] for ligne in decisions]
    verifier("une décision par demande, exactement",
             sorted(demandes_decidees) == sorted(identifiants["demande"]),
             f"{len(decisions)} décisions pour {len(demandes)} demandes")
    acceptees = {ligne["identifiant_demande"] for ligne in decisions if ligne["statut"] == "ACCEPTEE"}
    verifier("un crédit uniquement pour une demande acceptée",
             all(ligne["identifiant_demande"] in acceptees for ligne in credits))
    verifier("un seul crédit par demande",
             len({ligne["identifiant_demande"] for ligne in credits}) == len(credits))
    verifier("toute demande acceptée donne un crédit",
             len(acceptees) == len(credits), f"{len(acceptees)} acceptées, {len(credits)} crédits")

    # 7 — chronologie du dossier
    dates_demande = {ligne["identifiant_demande"]: jour(ligne["date_demande"]) for ligne in demandes}
    dates_decision = {ligne["identifiant_demande"]: jour(ligne["date_decision"]) for ligne in decisions}
    verifier("date_demande <= date_decision",
             all(dates_demande[cle] <= valeur for cle, valeur in dates_decision.items()))
    verifier("date_decision <= date_decaissement <= date_premiere_echeance",
             all(dates_decision[ligne["identifiant_demande"]] <= jour(ligne["date_decaissement"])
                 <= jour(ligne["date_premiere_echeance"]) for ligne in credits))

    # 8 — aucun paiement avant son décaissement
    decaissement = {ligne["identifiant_credit"]: jour(ligne["date_decaissement"]) for ligne in credits}
    verifier("aucun paiement antérieur au décaissement",
             all(jour(ligne["date_paiement"]) >= decaissement[ligne["identifiant_credit"]] for ligne in paiements))

    # 9 — échéanciers complets et équilibrés
    par_credit = {}
    for ligne in echeances:
        par_credit.setdefault(ligne["identifiant_credit"], []).append(ligne)
    durees = {ligne["identifiant_credit"]: int(ligne["duree_mois"]) for ligne in credits}
    montants = {ligne["identifiant_credit"]: int(ligne["montant_decaisse"]) for ligne in credits}
    verifier("le nombre d'échéances égale la durée du crédit",
             all(len(lignes) == durees[cle] for cle, lignes in par_credit.items()))
    verifier("la numérotation des échéances est continue",
             all(sorted(int(ligne["numero_echeance"]) for ligne in lignes) == list(range(1, len(lignes) + 1))
                 for lignes in par_credit.values()))
    verifier("la somme des capitaux dus égale le montant décaissé",
             all(sum(int(ligne["montant_capital_du"]) for ligne in lignes) == montants[cle]
                 for cle, lignes in par_credit.items()))

    # 10 — montants dans les bornes
    bornes = {ligne["identifiant_produit"]: (int(ligne["montant_min"]), int(ligne["montant_max"])) for ligne in produits}
    produit_par_demande = {ligne["identifiant_demande"]: ligne["identifiant_produit"] for ligne in demandes}
    montant_demande = {ligne["identifiant_demande"]: int(ligne["montant_demande"]) for ligne in demandes}
    verifier("montant demandé dans les bornes du produit",
             all(bornes[produit_par_demande[cle]][0] <= valeur <= bornes[produit_par_demande[cle]][1]
                 for cle, valeur in montant_demande.items()))
    verifier("montant accordé inférieur ou égal au montant demandé",
             all(int(ligne["montant_accorde"]) <= montant_demande[ligne["identifiant_demande"]]
                 for ligne in decisions if ligne["montant_accorde"]))

    # 11 et 12 — fenêtres de vie
    entree = {ligne["identifiant_client"]: jour(ligne["date_entree_relation"]) for ligne in clients}
    verifier("aucune demande avant l'entrée en relation",
             all(jour(ligne["date_demande"]) >= entree[ligne["identifiant_client"]] for ligne in demandes))
    verifier("aucun relevé avant l'entrée en relation",
             all(jour(ligne["date_releve"]) >= entree[ligne["identifiant_client"]] for ligne in releves))
    ouverture = {ligne["identifiant_agence"]: jour(ligne["date_ouverture"]) for ligne in agences}
    verifier("aucun client rattaché à une agence non encore ouverte",
             all(ouverture[ligne["identifiant_agence"]] <= entree[ligne["identifiant_client"]] for ligne in clients))
    fonction = {ligne["identifiant_agent"]: (jour(ligne["date_entree_fonction"]),
                                             jour(ligne["date_sortie_fonction"]) if ligne["date_sortie_fonction"] else FIN_DU_MONDE)
                for ligne in agents}
    verifier("aucune demande instruite par un agent hors fonction",
             all(fonction[ligne["identifiant_agent"]][0] <= jour(ligne["date_demande"]) <= fonction[ligne["identifiant_agent"]][1]
                 for ligne in demandes))

    toutes_dates = (
        [jour(ligne["date_demande"]) for ligne in demandes]
        + [jour(ligne["date_paiement"]) for ligne in paiements]
        + [jour(ligne["date_releve"]) for ligne in releves]
    )
    verifier("aucune date hors de l'horizon du monde",
             all(DEBUT_DU_MONDE <= valeur <= FIN_DU_MONDE for valeur in toutes_dates))

    # 14 — anti-fuite : le relevé d'instruction précède la décision
    date_releve = {ligne["identifiant_releve"]: jour(ligne["date_releve"]) for ligne in releves}
    verifier("le relevé d'instruction n'est jamais postérieur à la demande",
             all(date_releve[ligne["identifiant_releve_instruction"]] <= dates_demande[ligne["identifiant_demande"]]
                 for ligne in demandes if ligne["identifiant_releve_instruction"] in date_releve))

    # 13 — étanchéité des deux mondes
    colonnes_verite = set(profils_latents[0]) - {"identifiant_client", "identifiant_institution"}
    colonnes_brutes = set(clients[0]) | set(activites[0]) | set(demandes[0])
    verifier("aucun paramètre latent publié dans les tables observables",
             not (colonnes_verite & colonnes_brutes), str(colonnes_verite & colonnes_brutes))

    # 15 — cibles de l'institution
    observables = [ligne for ligne in resultats if ligne["observation_censuree"] == "0"]
    taux_acceptation = len(acceptees) / len(decisions) if decisions else 0
    taux_defaut = sum(1 for ligne in observables if ligne["defaut_experimental"] == "1") / len(observables) if observables else 0
    verifier("taux d'acceptation dans la plage visée", 0.55 <= taux_acceptation <= 0.92, f"{taux_acceptation:.1%}")
    verifier("taux de défaut dans la plage visée", 0.03 <= taux_defaut <= 0.22, f"{taux_defaut:.1%}")

    echecs = [controle for controle in controles if not controle[1]]
    for intitule, reussi, detail in controles:
        marque = "ok  " if reussi else "ECHEC"
        print(f"  {marque}  {intitule}" + (f"  [{detail}]" if detail else ""))
    print(f"\n{len(controles) - len(echecs)}/{len(controles)} contrôles passés.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
