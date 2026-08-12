"""Couche 4 : la dégradation volontaire des données.

Une base réelle n'est jamais propre. On abîme donc le monde après l'avoir
construit cohérent, et on journalise chaque dégradation dans verite/ — sans ce
journal, le laboratoire de qualité des données n'aurait aucun moyen de mesurer
son propre taux de détection.

Deux garde-fous : l'intégrité référentielle n'est jamais touchée, et les clés
primaires ne sont jamais altérées. Sinon les jointures cassent pour de
mauvaises raisons, et on passerait le laboratoire à déboguer le simulateur.
"""

from .aleatoire import flux

TAUX_VALEUR_MANQUANTE = 0.06
TAUX_MONTANT_ABERRANT = 0.004
TAUX_INCOHERENCE = 0.015
TAUX_ARRONDI = 0.03
TAUX_DOUBLON = 0.008

COLONNES_EFFACABLES = (
    "recettes_mensuelles_declarees",
    "charges_mensuelles_declarees",
    "stock_estime",
    "autres_revenus_menage",
    "charges_menage",
)


def degrader_releves(releves, facteur_institution, graine, premier_numero=1):
    """Abîme les relevés d'activité et retourne le journal des injections."""
    journal = []
    numero = premier_numero - 1
    doublons = []

    for releve in releves:
        aleatoire = flux(graine, "qualite", releve["identifiant_releve"])

        def noter(colonne, type_anomalie, valeur_vraie, valeur_publiee):
            nonlocal numero
            numero += 1
            journal.append({
                "identifiant_injection": f"INJ-{numero:06d}",
                "table_cible": "07b_releves_activite.csv",
                "identifiant_ligne": releve["identifiant_releve"],
                "colonne": colonne,
                "type_anomalie": type_anomalie,
                "valeur_vraie": valeur_vraie,
                "valeur_publiee": valeur_publiee,
            })

        # Charges supérieures aux recettes : ce n'est pas forcément une erreur.
        # Un mois de réapprovisionnement ou une perte réelle produisent la même
        # ligne. C'est au module de qualité d'apprendre à distinguer la donnée
        # improbable, qu'on garde en la signalant, de la donnée impossible.
        if releve["recettes_mensuelles_declarees"] != "" and aleatoire.random() < TAUX_INCOHERENCE * facteur_institution:
            ancienne = releve["charges_mensuelles_declarees"]
            nouvelle = int(round(float(releve["recettes_mensuelles_declarees"]) * aleatoire.uniform(1.2, 4.0)))
            releve["charges_mensuelles_declarees"] = nouvelle
            noter("charges_mensuelles_declarees", "incoherence_economique", ancienne, nouvelle)

        if releve["recettes_mensuelles_declarees"] != "" and aleatoire.random() < TAUX_ARRONDI * facteur_institution:
            ancienne = releve["recettes_mensuelles_declarees"]
            nouvelle = max(100000, int(round(float(ancienne) / 100000) * 100000))
            releve["recettes_mensuelles_declarees"] = nouvelle
            noter("recettes_mensuelles_declarees", "arrondi_suspect", ancienne, nouvelle)

        if aleatoire.random() < TAUX_MONTANT_ABERRANT * facteur_institution:
            colonne = aleatoire.choice(("recettes_mensuelles_declarees", "charges_mensuelles_declarees"))
            if releve[colonne] != "":
                ancienne = releve[colonne]
                nouvelle = int(float(ancienne) * aleatoire.choice((10, 100)))
                releve[colonne] = nouvelle
                noter(colonne, "montant_aberrant", ancienne, nouvelle)

        for colonne in COLONNES_EFFACABLES:
            if releve[colonne] != "" and aleatoire.random() < TAUX_VALEUR_MANQUANTE * facteur_institution:
                ancienne = releve[colonne]
                releve[colonne] = ""
                noter(colonne, "valeur_manquante", ancienne, "")

        # Doublon de saisie : la ligne est recopiée avec un nouvel identifiant,
        # comme le ferait un agent qui enregistre deux fois la même visite.
        if aleatoire.random() < TAUX_DOUBLON * facteur_institution:
            doublons.append(dict(releve))

    numero_releve = max((int(ligne["identifiant_releve"].split("-")[1]) for ligne in releves), default=0)
    for copie in doublons:
        numero_releve += 1
        origine = copie["identifiant_releve"]
        copie["identifiant_releve"] = f"REL-{numero_releve:06d}"
        releves.append(copie)
        numero += 1
        journal.append({
            "identifiant_injection": f"INJ-{numero:06d}",
            "table_cible": "07b_releves_activite.csv",
            "identifiant_ligne": copie["identifiant_releve"],
            "colonne": "",
            "type_anomalie": "doublon_ligne",
            "valeur_vraie": origine,
            "valeur_publiee": copie["identifiant_releve"],
        })

    return releves, journal
