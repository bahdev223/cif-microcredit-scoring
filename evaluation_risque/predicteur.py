from .caracteristiques import construire_caracteristiques
from .regles import evaluer_regles


def predire_risque(client, demande_credit):
    caracteristiques = construire_caracteristiques(client, demande_credit)
    resultat = evaluer_regles(caracteristiques)
    score = resultat["score_risque"]
    resultat["niveau_risque"] = "FAIBLE" if score < 30 else "MODERE" if score < 60 else "ELEVE"
    resultat["recommandation"] = {
        "FAIBLE": "A examiner favorablement par l'agent.",
        "MODERE": "Demander une verification complementaire avant decision.",
        "ELEVE": "A ne pas valider sans analyse humaine approfondie.",
    }[resultat["niveau_risque"]]
    resultat["caracteristiques"] = caracteristiques
    return resultat
