"""Feature Engine : transforme un dossier en variables métier.

C'est la seule couche autorisée à lire les objets Django. Les moteurs qui
suivent ne manipulent que le dictionnaire produit ici, ce qui garantit qu'ils
observent tous exactement les mêmes chiffres.

Quatre familles de variables, celles identifiées au départ du projet :

    capacite_financiere   ce qui entre, ce qui sort, ce qui reste
    comportement          ce que le client a déjà fait de ses crédits
    activite              ce qu'il fait et depuis combien de temps
    credit_demande        ce qu'il demande aujourd'hui

Une valeur inconnue vaut None, jamais zéro. La différence est capitale : un
ménage sans charges déclarées n'est pas un ménage sans charges.
"""

from collections import Counter

from credits.rapprochement import rapprocher_credit

MOIS_LIBELLES = ("janv.", "févr.", "mars", "avril", "mai", "juin",
                 "juil.", "août", "sept.", "oct.", "nov.", "déc.")


def construire_variables(demande, date_observation):
    client = demande.client
    rapprochements = [
        rapprocher_credit(credit, date_observation)
        for credit in client.credits_importes.prefetch_related("echeances", "paiements").all()
    ]
    return {
        "capacite_financiere": variables_capacite(demande),
        "comportement": variables_comportement(rapprochements),
        "activite": variables_activite(demande, client, rapprochements),
        "credit_demande": variables_credit(demande),
    }


def variables_capacite(demande):
    """La cascade qui sépare le chiffre d'affaires de la capacité réelle."""
    recettes = demande.recettes_activite or None
    charges_activite = demande.charges_activite or None
    autres_revenus = demande.autres_revenus_menage or None
    charges_menage = demande.charges_menage or None
    engagements = demande.mensualite_dette_existante or None

    resultat_activite = None
    if recettes is not None:
        resultat_activite = recettes - (charges_activite or 0)

    marge = None
    if recettes is not None:
        marge = resultat_activite + (autres_revenus or 0) - (charges_menage or 0) - (engagements or 0)

    return {
        "recettes": recettes,
        "charges_activite": charges_activite,
        "resultat_activite": resultat_activite,
        "autres_revenus": autres_revenus,
        "charges_menage": charges_menage,
        "engagements": engagements,
        "marge_disponible": marge,
        "taux_marge_activite": round(resultat_activite / recettes, 3) if recettes else None,
        "renseignee": recettes is not None,
    }


def variables_comportement(rapprochements):
    """Ce que les remboursements passés disent, sans le résumer en note."""
    if not rapprochements:
        return {"historique_disponible": False}

    echeances_echues = [
        echeance
        for rapprochement in rapprochements
        for echeance in rapprochement["echeances"]
        if echeance["date_couverture"] or echeance["en_retard"]
    ]
    a_lheure = sum(1 for echeance in echeances_echues if echeance["jours_retard"] == 0)

    return {
        "historique_disponible": True,
        "nombre_credits": len(rapprochements),
        "nombre_soldes": sum(1 for r in rapprochements if r["statut"].startswith("SOLDE")),
        "nombre_en_cours": sum(1 for r in rapprochements if r["statut"] in ("EN_COURS", "EN_RETARD")),
        "nombre_credits_avec_retard": sum(1 for r in rapprochements if r["jours_retard_max"] > 0),
        "jours_retard_max": max(r["jours_retard_max"] for r in rapprochements),
        "echeances_echues": len(echeances_echues),
        "echeances_a_lheure": a_lheure,
        "taux_ponctualite": round(a_lheure / len(echeances_echues), 3) if echeances_echues else None,
        "echeances_en_retard": sum(r["nombre_echeances_en_retard"] for r in rapprochements),
        "montant_reste_du": sum(r["reste_du"] for r in rapprochements),
        "montant_emprunte_cumule": sum(r["montant_decaisse"] for r in rapprochements),
        "montant_dernier_credit": rapprochements[-1]["montant_decaisse"] if rapprochements else None,
    }


def variables_activite(demande, client, rapprochements):
    """Secteur, ancienneté, et ce que les versements disent de la saisonnalité."""
    anciennete = demande.anciennete_activite_mois or client.anciennete_activite_mois or None
    versements = [
        paiement
        for rapprochement in rapprochements
        for paiement in rapprochement["paiements"]
        if paiement["date"]
    ]

    profil_mensuel, concentration = None, None
    if len(versements) >= 12:
        compte = Counter(int(paiement["date"][5:7]) for paiement in versements)
        profil_mensuel = [
            {"mois": MOIS_LIBELLES[numero - 1], "versements": compte.get(numero, 0)}
            for numero in range(1, 13)
        ]
        pic = max(compte.values())
        concentration = round(pic / len(versements), 3)

    return {
        "secteur": client.secteur_activite or None,
        "anciennete_mois": anciennete,
        "saisonnalite_declaree": demande.saisonnalite_activite or None,
        "profil_versements_mensuels": profil_mensuel,
        "concentration_mensuelle": concentration,
        "versements_observes": len(versements),
    }


def variables_credit(demande):
    recettes = demande.recettes_activite or None
    return {
        "montant": demande.montant_demande,
        "duree_mois": demande.duree_mois,
        "objet": demande.objet_credit or None,
        "produit": demande.produit.libelle if demande.produit_id else None,
        "echeance_estimee": demande.echeance_estimee,
        "ratio_montant_recettes": round(demande.montant_demande / recettes, 2) if recettes else None,
    }
