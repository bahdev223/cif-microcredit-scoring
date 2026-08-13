"""Règles appliquées à l'analyse préliminaire.

Les seuils écrits ici sont pédagogiques. Ils n'ont été validés par aucune
institution et ne reflètent aucune politique de crédit réelle. Le catalogue
ci-dessous est la source unique de l'écran « Règles d'analyse » : ce que
l'application affiche est exactement ce qu'elle applique.
"""

CATALOGUE_REGLES = (
    {
        "code": "R01",
        "libelle": "Capacité de remboursement",
        "description": "Compare la marge estimée à l'échéance estimée du crédit demandé.",
        "seuils": "Favorable au-delà de 2 fois l'échéance, vigilance en dessous d'une fois.",
        "active": True,
    },
    {
        "code": "R02",
        "libelle": "Ancienneté de l'activité",
        "description": "Distingue une activité établie d'une activité récente.",
        "seuils": "Favorable à partir de 24 mois, vigilance en dessous de 12 mois.",
        "active": True,
    },
    {
        "code": "R03",
        "libelle": "Historique de retard",
        "description": "Tient compte des retards déjà connus pour ce client.",
        "seuils": "Vigilance dès un retard, renforcée au-delà de deux.",
        "active": True,
    },
    {
        "code": "R04",
        "libelle": "Régularité des cotisations tontine",
        "description": "Signal comportemental relevé à la saisie du dossier.",
        "seuils": "Favorable si régulière ; l'absence d'information est signalée.",
        "active": True,
    },
)


def evaluer_regles(caracteristiques):
    score = 45
    facteurs_favorables, points_vigilance, regles_declenchees = [], [], []

    if caracteristiques["ratio_capacite"] >= 2:
        score -= 18
        facteurs_favorables.append("Capacite mensuelle confortable par rapport a l'echeance.")
    elif caracteristiques["ratio_capacite"] >= 1:
        score -= 5
        facteurs_favorables.append("Capacite mensuelle suffisante mais a surveiller.")
    else:
        score += 25
        points_vigilance.append("Capacite mensuelle inferieure a l'echeance estimee.")
        regles_declenchees.append("R01 - capacite de remboursement insuffisante")

    if caracteristiques["anciennete_activite_mois"] >= 24:
        score -= 10
        facteurs_favorables.append("Activite exercee depuis au moins 24 mois.")
    elif caracteristiques["anciennete_activite_mois"] < 12:
        score += 12
        points_vigilance.append("Activite recente : recul limite sur les revenus.")
        regles_declenchees.append("R02 - anciennete faible")

    if caracteristiques["nombre_retards"] == 0:
        score -= 8
        facteurs_favorables.append("Aucun retard de paiement renseigne.")
    else:
        score += 12 if caracteristiques["nombre_retards"] <= 2 else 25
        points_vigilance.append("Retards precedents declares.")
        regles_declenchees.append("R03 - historique de retard")

    if caracteristiques["regularite_tontine"] == "reguliere":
        score -= 7
        facteurs_favorables.append("Cotisations tontine regulieres.")
    elif caracteristiques["regularite_tontine"] == "inconnue":
        score += 4
        points_vigilance.append("Information tontine indisponible.")

    return {"score_risque": max(5, min(95, round(score))), "facteurs_favorables": facteurs_favorables, "points_vigilance": points_vigilance, "regles_declenchees": regles_declenchees or ["Aucune regle bloquante declenchee"]}
