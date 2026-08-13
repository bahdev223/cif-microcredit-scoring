"""Versions des composants analytiques.

Chaque analyse enregistre les versions qui l'ont produite. Quand un moteur
évolue, les analyses passées restent rattachées à la version qui les a
calculées : c'est la condition pour pouvoir expliquer, des mois plus tard,
pourquoi un dossier a été présenté ainsi.
"""

VERSION_FEATURE_ENGINE = "1.0"
VERSION_MOTEURS_METIER = "1.0"
VERSION_MODELE_STATISTIQUE = None


def versions_courantes():
    return {
        "feature_engine": VERSION_FEATURE_ENGINE,
        "moteurs_metier": VERSION_MOTEURS_METIER,
        "modele_statistique": VERSION_MODELE_STATISTIQUE,
        "modele_statistique_actif": VERSION_MODELE_STATISTIQUE is not None,
    }
