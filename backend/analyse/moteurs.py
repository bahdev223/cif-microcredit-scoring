"""Les six moteurs spécialisés.

Chaque moteur observe une seule dimension du dossier et produit trois choses :

    evaluable    dit s'il dispose de quoi se prononcer
    indicateurs  les chiffres qu'il a calculés
    constats     ce qu'il en dit, en une phrase par constat

Aucun moteur ne note, ne pondère, ni ne conclut. Un moteur qui manque de
données le déclare et s'arrête : c'est la différence entre un système qui sait
ce qu'il ignore et un système qui invente une valeur par défaut.

Les seuils employés ici sont des repères de lecture, pas une politique de
crédit. Ils sont écrits en clair pour qu'une institution puisse les corriger.
"""

SEUIL_PRESSION_TENDUE = 0.5
SEUIL_PRESSION_CRITIQUE = 0.8
SEUIL_ANCIENNETE_ETABLIE = 24
SEUIL_ANCIENNETE_RECENTE = 12
SEUIL_CONCENTRATION_SAISONNIERE = 0.22


def executer_moteurs(variables, qualite_dossier):
    return [
        moteur_capacite(variables),
        moteur_historique(variables),
        moteur_comportement(variables),
        moteur_endettement(variables),
        moteur_activite_saisonnalite(variables),
        moteur_anomalies(variables, qualite_dossier),
    ]


def indicateur(libelle, valeur, format_="texte", precision=None):
    return {"libelle": libelle, "valeur": valeur, "format": format_, "precision": precision}


def constat(sens, texte):
    return {"sens": sens, "texte": texte}


def moteur_capacite(variables):
    capacite = variables["capacite_financiere"]
    credit = variables["credit_demande"]

    if not capacite["renseignee"]:
        return {
            "code": "capacite",
            "libelle": "Capacité de remboursement",
            "evaluable": False,
            "message": "Aucune recette n'est renseignée : la capacité de remboursement ne peut pas être appréciée.",
            "indicateurs": [],
            "constats": [],
        }

    marge = capacite["marge_disponible"]
    echeance = credit["echeance_estimee"]
    pression = round(echeance / marge, 3) if marge and marge > 0 else None

    if marge is None or marge <= 0:
        niveau = "insuffisante"
    elif pression is None:
        niveau = "indeterminee"
    elif pression > 1:
        niveau = "depassee"
    elif pression >= SEUIL_PRESSION_CRITIQUE:
        niveau = "critique"
    elif pression >= SEUIL_PRESSION_TENDUE:
        niveau = "tendue"
    else:
        niveau = "soutenable"

    constats = []
    if niveau == "insuffisante":
        constats.append(constat("attention", "Les charges déclarées absorbent la totalité des recettes."))
    elif niveau == "depassee":
        constats.append(constat("attention", f"L'échéance estimée dépasse la marge disponible de {echeance - marge:,} F.".replace(",", " ")))
    elif niveau == "critique":
        constats.append(constat("attention", "L'échéance absorbe plus de 80 % de la marge disponible."))
    elif niveau == "tendue":
        constats.append(constat("attention", "L'échéance absorbe plus de la moitié de la marge disponible."))
    else:
        constats.append(constat("favorable", "L'échéance reste inférieure à la moitié de la marge disponible."))

    if capacite["taux_marge_activite"] is not None and capacite["taux_marge_activite"] < 0.15:
        constats.append(constat("attention", "Marge d'activité faible : le chiffre d'affaires est élevé mais peu rentable."))

    return {
        "code": "capacite",
        "libelle": "Capacité de remboursement",
        "evaluable": True,
        "message": "",
        "cascade": [
            {"libelle": "Recettes de l'activité", "montant": capacite["recettes"], "sens": "credit"},
            {"libelle": "Charges de l'activité", "montant": capacite["charges_activite"] or 0, "sens": "debit"},
            {"libelle": "Résultat de l'activité", "montant": capacite["resultat_activite"], "sens": "sous_total"},
            {"libelle": "Autres revenus du ménage", "montant": capacite["autres_revenus"] or 0, "sens": "credit"},
            {"libelle": "Charges du ménage", "montant": capacite["charges_menage"] or 0, "sens": "debit"},
            {"libelle": "Engagements existants", "montant": capacite["engagements"] or 0, "sens": "debit"},
            {"libelle": "Marge disponible", "montant": marge, "sens": "total"},
        ],
        "pression": {
            "valeur": pression,
            "niveau": niveau,
            "echeance_estimee": echeance,
            "marge_disponible": marge,
        },
        "indicateurs": [
            indicateur("Marge disponible", marge, "montant"),
            indicateur("Échéance estimée", echeance, "montant"),
            indicateur("Taux de marge de l'activité", capacite["taux_marge_activite"], "pourcentage"),
        ],
        "constats": constats,
    }


def moteur_historique(variables):
    comportement = variables["comportement"]

    if not comportement["historique_disponible"]:
        return {
            "code": "historique",
            "libelle": "Historique de crédit",
            "evaluable": False,
            "message": "Aucun crédit antérieur dans l'institution. Le comportement de remboursement ne peut pas être évalué.",
            "indicateurs": [],
            "constats": [],
        }

    constats = []
    if comportement["nombre_soldes"] and not comportement["nombre_credits_avec_retard"]:
        constats.append(constat("favorable", f"{comportement['nombre_soldes']} crédit(s) soldé(s) sans aucun retard."))
    elif comportement["nombre_soldes"]:
        constats.append(constat("favorable", f"{comportement['nombre_soldes']} crédit(s) déjà soldé(s)."))
    if comportement["nombre_credits_avec_retard"]:
        constats.append(constat("attention", f"{comportement['nombre_credits_avec_retard']} crédit(s) ont connu au moins un retard."))
    if comportement["echeances_en_retard"]:
        constats.append(constat("attention", f"{comportement['echeances_en_retard']} échéance(s) sont actuellement impayées."))

    return {
        "code": "historique",
        "libelle": "Historique de crédit",
        "evaluable": True,
        "message": "",
        "indicateurs": [
            indicateur("Crédits obtenus", comportement["nombre_credits"], "nombre"),
            indicateur("Crédits soldés", comportement["nombre_soldes"], "nombre"),
            indicateur("Crédits en cours", comportement["nombre_en_cours"], "nombre"),
            indicateur("Montant cumulé emprunté", comportement["montant_emprunte_cumule"], "montant"),
        ],
        "constats": constats,
    }


def moteur_comportement(variables):
    comportement = variables["comportement"]

    if not comportement["historique_disponible"] or not comportement["echeances_echues"]:
        return {
            "code": "comportement",
            "libelle": "Comportement de paiement",
            "evaluable": False,
            "message": "Aucune échéance échue observée : la régularité des versements ne peut pas être mesurée.",
            "indicateurs": [],
            "constats": [],
        }

    ponctualite = comportement["taux_ponctualite"]
    retard_max = comportement["jours_retard_max"]

    constats = []
    if ponctualite is not None and ponctualite >= 0.9:
        constats.append(constat("favorable", "Les échéances ont été honorées à la date prévue dans la quasi-totalité des cas."))
    elif ponctualite is not None and ponctualite < 0.6:
        constats.append(constat("attention", "Moins de six échéances sur dix ont été payées à la date prévue."))
    if retard_max >= 90:
        constats.append(constat("attention", f"Un retard de {retard_max} jours a été observé."))
    elif retard_max:
        constats.append(constat("neutre", f"Retard le plus long observé : {retard_max} jours."))
    else:
        constats.append(constat("favorable", "Aucun retard observé sur les échéances échues."))

    return {
        "code": "comportement",
        "libelle": "Comportement de paiement",
        "evaluable": True,
        "message": "",
        "indicateurs": [
            indicateur("Échéances échues", comportement["echeances_echues"], "nombre"),
            indicateur("Payées à la date prévue", comportement["echeances_a_lheure"], "nombre"),
            indicateur("Taux de ponctualité", ponctualite, "pourcentage"),
            indicateur("Retard le plus long", retard_max, "jours"),
        ],
        "constats": constats,
    }


def moteur_endettement(variables):
    capacite = variables["capacite_financiere"]
    credit = variables["credit_demande"]
    comportement = variables["comportement"]

    engagements = capacite["engagements"] or 0
    echeance = credit["echeance_estimee"]
    recettes = capacite["recettes"]
    reste_du = comportement.get("montant_reste_du", 0) if comportement["historique_disponible"] else 0

    if not recettes:
        return {
            "code": "endettement",
            "libelle": "Endettement",
            "evaluable": False,
            "message": "Sans recettes renseignées, le poids des engagements ne peut pas être rapporté aux revenus.",
            "indicateurs": [],
            "constats": [],
        }

    taux_actuel = round(engagements / recettes, 3)
    taux_apres = round((engagements + echeance) / recettes, 3)

    constats = []
    if engagements:
        constats.append(constat("neutre", f"Le client supporte déjà {engagements:,} F de mensualités.".replace(",", " ")))
    else:
        constats.append(constat("favorable", "Aucun engagement mensuel déclaré."))
    if reste_du:
        constats.append(constat("attention", f"Un encours de {reste_du:,} F reste dû dans l'institution.".replace(",", " ")))
    if taux_apres > 0.33:
        constats.append(constat("attention", "Après ce crédit, les mensualités dépasseraient un tiers des recettes."))

    return {
        "code": "endettement",
        "libelle": "Endettement",
        "evaluable": True,
        "message": "",
        "indicateurs": [
            indicateur("Mensualités actuelles", engagements, "montant"),
            indicateur("Après ce crédit", engagements + echeance, "montant"),
            indicateur("Poids sur les recettes", taux_apres, "pourcentage"),
            indicateur("Encours interne restant dû", reste_du, "montant"),
        ],
        "constats": constats,
        "note": "Les engagements hors institution sont déclaratifs : ils ne sont pas vérifiables dans l'application.",
    }


def moteur_activite_saisonnalite(variables):
    activite = variables["activite"]
    anciennete = activite["anciennete_mois"]

    constats = []
    if anciennete is None:
        constats.append(constat("attention", "Ancienneté de l'activité non renseignée."))
    elif anciennete >= SEUIL_ANCIENNETE_ETABLIE:
        constats.append(constat("favorable", f"Activité exercée depuis {anciennete // 12} an(s)."))
    elif anciennete < SEUIL_ANCIENNETE_RECENTE:
        constats.append(constat("attention", "Activité récente : moins de douze mois de recul."))

    declaree = activite["saisonnalite_declaree"]
    if declaree == "saisonniere":
        constats.append(constat("attention", "Activité déclarée saisonnière : les recettes mensuelles ne sont pas régulières."))
    elif declaree == "irreguliere":
        constats.append(constat("attention", "Revenus déclarés irréguliers."))
    elif declaree == "stable":
        constats.append(constat("favorable", "Activité déclarée stable sur l'année."))
    else:
        constats.append(constat("neutre", "Saisonnalité non renseignée au dossier."))

    concentration = activite["concentration_mensuelle"]
    if concentration is not None and concentration >= SEUIL_CONCENTRATION_SAISONNIERE:
        constats.append(constat("attention", "Les versements passés se concentrent sur quelques mois de l'année."))

    return {
        "code": "activite",
        "libelle": "Activité et saisonnalité",
        "evaluable": True,
        "message": "",
        "indicateurs": [
            indicateur("Secteur", activite["secteur"] or "non renseigné", "texte"),
            indicateur("Ancienneté", anciennete, "mois"),
            indicateur("Saisonnalité déclarée", declaree or "non renseignée", "texte"),
        ],
        "profil_versements": activite["profil_versements_mensuels"],
        "message_profil": (
            "Répartition des versements passés par mois. Elle ne remplace pas un relevé de recettes mensuelles."
            if activite["profil_versements_mensuels"]
            else "Trop peu de versements observés pour dégager un rythme mensuel."
        ),
        "constats": constats,
    }


def moteur_anomalies(variables, qualite_dossier):
    capacite = variables["capacite_financiere"]

    constats = []
    for controle in qualite_dossier["controles"]:
        if not controle["present"]:
            constats.append(constat("attention", f"{controle['libelle']} : information absente."))

    if capacite["recettes"] and capacite["charges_activite"] and capacite["charges_activite"] > capacite["recettes"]:
        constats.append(constat("attention", "Les charges déclarées dépassent les recettes : à confirmer avec le client."))
    if capacite["engagements"]:
        constats.append(constat("neutre", "Les engagements hors institution sont déclaratifs."))
    if not constats:
        constats.append(constat("favorable", "Aucune incohérence relevée dans le dossier."))

    return {
        "code": "anomalies",
        "libelle": "Qualité des données",
        "evaluable": True,
        "message": "",
        "indicateurs": [
            indicateur("Complétude du dossier", qualite_dossier["completude"] / 100, "pourcentage"),
            indicateur("Informations renseignées", f"{qualite_dossier['renseignes']} / {qualite_dossier['total']}", "texte"),
        ],
        "constats": constats,
    }
