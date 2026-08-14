"""Les six moteurs spécialisés.

Le moteur de capacité ne calcule rien lui-même : il exécute le cadre
d'analyse applicable et lit ce qu'il produit. La méthode de calcul
appartient à l'institution, pas à ce fichier.

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

from cadres.moteur import executer, executer_cadre

from . import cadre_par_defaut

SEUIL_PRESSION_TENDUE = 0.5
SEUIL_PRESSION_CRITIQUE = 0.8
SEUIL_ANCIENNETE_ETABLIE = 24
SEUIL_ANCIENNETE_RECENTE = 12
SEUIL_CONCENTRATION_SAISONNIERE = 0.22


def executer_moteurs(variables, qualite_dossier, demande):
    return [
        moteur_capacite(variables, demande),
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


def moteur_capacite(variables, demande):
    """Exécute le cadre d'analyse applicable et lit ce qu'il produit.

    Aucune cascade n'est calculée ici : la méthode appartient à l'institution.
    Si son produit de crédit désigne un cadre, c'est celui-là qui s'applique,
    dans la version enregistrée sur la demande. Sinon, le cadre par défaut est
    exécuté — lui aussi une simple configuration, par le même moteur.
    """
    resultat = executer_cadre_applicable(demande)
    lignes = [ligne for ligne in resultat["lignes"] if ligne["mode"] != "INFORMATION"]

    if not resultat["valeurs"].get("RECETTES_ACT") and not any(
        ligne["valeur"] for ligne in lignes if ligne["mode"] == "SAISIE"
    ):
        return {
            "code": "capacite",
            "libelle": "Capacité de remboursement",
            "evaluable": False,
            "message": "Aucun montant n'a été relevé : la capacité de remboursement ne peut pas être appréciée.",
            "indicateurs": [],
            "constats": [],
            "cadre": resultat["cadre"],
        }

    marge = valeur_par_role(resultat, "MARGE_DISPONIBLE")
    pression = valeur_par_role(resultat, "PRESSION_REMBOURSEMENT")
    echeance = variables["credit_demande"]["echeance_estimee"]

    constats = [
        constat("attention" if regle["resultat"] == "POINT_ATTENTION" else "favorable", regle["message"])
        for regle in resultat["regles_declenchees"]
    ]
    if variables["capacite_financiere"]["taux_marge_activite"] is not None \
            and variables["capacite_financiere"]["taux_marge_activite"] < 0.15:
        constats.append(constat("attention", "Marge d'activité faible : le chiffre d'affaires est élevé mais peu rentable."))
    for anomalie in resultat["anomalies"]:
        constats.append(constat("attention", anomalie["message"]))

    return {
        "code": "capacite",
        "libelle": "Capacité de remboursement",
        "evaluable": True,
        "message": "",
        "cadre": resultat["cadre"],
        "cascade": [{
            "libelle": ligne["nom"],
            "montant": ligne["valeur"],
            "sens": "sous_total" if ligne["sens"] == "RESULTAT" else ligne["sens"].lower(),
            "section": ligne["section_nom"],
        } for ligne in lignes if ligne["type"] != "POURCENTAGE"],
        "pression": {
            "valeur": round(pression / 100, 3) if pression else None,
            "niveau": niveau_pression(marge, pression),
            "echeance_estimee": echeance,
            "marge_disponible": marge,
        },
        "indicateurs": [
            indicateur("Marge disponible", marge, "montant"),
            indicateur("Échéance projetée", echeance, "montant"),
            indicateur("Pression de remboursement", round(pression / 100, 3) if pression else None, "pourcentage"),
        ],
        "constats": constats,
    }


def valeur_par_role(resultat, role):
    """Lit une valeur par le rôle déclaré, jamais par le nom de la rubrique.

    L'institution appelle sa marge « Marge disponible », « Reste à vivre » ou
    « Capacité nette » : seul le rôle qu'elle attribue à la rubrique permet à
    la plateforme de savoir de quoi il s'agit.
    """
    for ligne in resultat["lignes"]:
        if ligne.get("role") == role:
            return ligne["valeur"]
    return None


def niveau_pression(marge, pression):
    if marge is None or marge <= 0:
        return "insuffisante"
    if pression is None:
        return "indeterminee"
    if pression > 100:
        return "depassee"
    if pression >= 100 * SEUIL_PRESSION_CRITIQUE:
        return "critique"
    if pression >= 100 * SEUIL_PRESSION_TENDUE:
        return "tendue"
    return "soutenable"


def executer_cadre_applicable(demande):
    """Choisit le cadre à appliquer, puis l'exécute.

    Le cadre retenu est enregistré sur la demande : deux consultations de la
    même instruction, à des mois d'écart, donnent le même résultat même si
    l'institution a publié une version plus récente entre-temps.
    """
    contexte = {"ECHEANCE_PROJETEE": demande.echeance_estimee}
    cadre = demande.cadre_analyse or (demande.produit.cadre_analyse if demande.produit_id else None)

    if cadre is not None:
        resultat = executer_cadre(cadre, valeurs_saisies_demande(demande, cadre), contexte)
        return resultat

    resultat = executer(cadre_par_defaut.DEFINITION, cadre_par_defaut.valeurs_depuis_demande(demande),
                        cadre_par_defaut.REGLES, contexte)
    resultat["cadre"] = {
        "code": cadre_par_defaut.CODE,
        "nom": cadre_par_defaut.NOM,
        "version": 0,
        "reference": cadre_par_defaut.NOM,
        "statut": "PAR_DEFAUT",
    }
    return resultat


def valeurs_saisies_demande(demande, cadre):
    """Valeurs à injecter dans un cadre configuré par l'institution."""
    if demande.valeurs_cadre:
        return dict(demande.valeurs_cadre)
    # Tant que le formulaire dynamique n'existe pas, on rapproche les champs
    # relevés sur la demande des rubriques qui portent le même code.
    return {
        code: valeur
        for code, valeur in cadre_par_defaut.valeurs_depuis_demande(demande).items()
        if any(rubrique["code"] == code for rubrique in cadre.definition())
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
