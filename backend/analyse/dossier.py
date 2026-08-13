"""Orchestrateur : assemble l'analyse complète d'un dossier.

    dossier
       │
       ├── Feature Engine ──────► variables métier
       │                              │
       ├── Rules Engine ───────► règles expérimentales (existant)
       │                              │
       │        Scoring Engine  ····► non activé
       │                              │
       └──────────────────────────────┴──► analyse du dossier

Le moteur statistique n'existe pas : aucune donnée réelle n'a servi à
l'entraîner. Sa place est réservée et déclarée inactive, de sorte qu'il puisse
être branché plus tard sans toucher au reste de la chaîne.
"""

from evaluation_risque.analyse_dossier import analyser_qualite_dossier
from evaluation_risque.predicteur import predire_risque

from .confiance import evaluer_confiance, situation_premiere_demande
from .moteurs import executer_moteurs
from .variables import construire_variables
from .versions import versions_courantes


def analyser(demande, date_observation):
    variables = construire_variables(demande, date_observation)
    qualite_dossier = analyser_qualite_dossier(demande)
    moteurs = executer_moteurs(variables, qualite_dossier)
    confiance = evaluer_confiance(moteurs, qualite_dossier, variables)

    return {
        "variables": variables,
        "moteurs": moteurs,
        "confiance": confiance,
        "premiere_demande": situation_premiere_demande(variables),
        "points": rassembler_points(moteurs),
        "qualite_dossier": qualite_dossier,
        "modele_statistique": {
            "actif": False,
            "message": "Aucun modèle statistique n'est activé. Aucune probabilité de défaut n'est produite.",
        },
        "regles_experimentales": executer_regles(demande),
        "versions": versions_courantes(),
    }


def rassembler_points(moteurs):
    """Ce qui appelle l'attention, ce qui rassure, chacun rattaché à son moteur.

    L'agent ne doit pas relire cinquante chiffres pour retrouver les trois
    lignes qui comptent.
    """
    attention, favorables = [], []
    for moteur in moteurs:
        if not moteur["evaluable"]:
            attention.append({"origine": moteur["libelle"], "texte": moteur["message"], "sens": "absent"})
            continue
        for element in moteur["constats"]:
            entree = {"origine": moteur["libelle"], "texte": element["texte"], "sens": element["sens"]}
            if element["sens"] == "attention":
                attention.append(entree)
            elif element["sens"] == "favorable":
                favorables.append(entree)
    return {"attention": attention, "favorables": favorables}


def executer_regles(demande):
    """Règles pédagogiques existantes, conservées à part et clairement datées."""
    prediction = predire_risque(demande.client, demande)
    return {
        "indicateur_composite": prediction["score_risque"],
        "niveau_indicatif": prediction["niveau_risque"],
        "regles_declenchees": prediction["regles_declenchees"],
        "avertissement": (
            "Indicateur expérimental issu de règles pédagogiques. "
            "Aucun modèle n'a été validé sur les données d'une institution."
        ),
    }
