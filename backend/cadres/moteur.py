"""Exécution d'un cadre d'analyse.

    cadre + valeurs
          ↓
      validation
          ↓
    ordonnancement des calculs
          ↓
    exécution des formules
          ↓
    évaluation des règles
          ↓
    sortie structurée

Le moteur ne connaît aucun secteur d'activité, aucun produit de crédit et
aucune politique d'octroi. Il exécute une définition de cadre, rien d'autre.

Deux entrées sont possibles : une définition en mémoire (utile pour l'aperçu
d'un brouillon, pour les tests, et pour rejouer un snapshot), ou un objet
CadreAnalyse. La première est la seule que le moteur connaisse réellement ;
la seconde n'est qu'une conversion.
"""

from .calcul import FormuleInvalide, analyser_condition, evaluer, ordonner


def executer(definition, valeurs_saisies, regles=(), contexte=None):
    """Calcule un cadre et évalue ses règles.

    definition      liste de rubriques : code, nom, mode, type, sens, formule…
    valeurs_saisies dictionnaire code → valeur, pour les rubriques de saisie
    regles          liste de règles : code, nom, condition, resultat, message
    contexte        valeurs supplémentaires lisibles par les formules et les
                    règles sans figurer au cadre (échéance projetée, par
                    exemple, qui vient de la demande et non du dossier)

    Retourne un dictionnaire structuré : valeurs, lignes affichables, règles
    déclenchées, anomalies. Une anomalie n'interrompt jamais le calcul : le
    moteur produit ce qu'il peut et signale le reste.
    """
    anomalies = []
    valeurs = dict(contexte or {})

    codes_definis = {rubrique["code"] for rubrique in definition}
    for rubrique in definition:
        if rubrique["mode"] == "CALCUL":
            continue
        valeur = valeurs_saisies.get(rubrique["code"])
        if valeur in (None, "") and rubrique.get("obligatoire"):
            anomalies.append({
                "code": rubrique["code"],
                "type": "VALEUR_MANQUANTE",
                "message": f"{rubrique['nom']} est obligatoire et n'est pas renseigné.",
            })
        valeurs[rubrique["code"]] = 0 if valeur in (None, "") else valeur

    try:
        ordre, arbres = ordonner(definition, codes_de_contexte=set(contexte or {}))
    except FormuleInvalide as erreur:
        return {
            "valide": False,
            "valeurs": valeurs,
            "lignes": [],
            "regles_declenchees": [],
            "anomalies": [{"code": "", "type": "CADRE_INVALIDE", "message": str(erreur)}],
            "ordre_calcul": [],
        }

    for code in ordre:
        valeurs[code] = evaluer(arbres[code], valeurs)

    lignes = [{
        "code": rubrique["code"],
        "nom": rubrique["nom"],
        "mode": rubrique["mode"],
        "type": rubrique.get("type", "MONTANT"),
        "sens": rubrique.get("sens", "CREDIT"),
        "unite": rubrique.get("unite", ""),
        "section_code": rubrique.get("section_code", ""),
        "section_nom": rubrique.get("section_nom", ""),
        "formule": rubrique.get("formule", ""),
        "valeur": arrondir(valeurs.get(rubrique["code"], 0), rubrique.get("type", "MONTANT")),
    } for rubrique in definition]

    declenchees = evaluer_regles(regles, valeurs, codes_definis, anomalies)

    return {
        "valide": not any(anomalie["type"] == "CADRE_INVALIDE" for anomalie in anomalies),
        "valeurs": {code: arrondir(valeur, "MONTANT") for code, valeur in valeurs.items()},
        "lignes": lignes,
        "regles_declenchees": declenchees,
        "anomalies": anomalies,
        "ordre_calcul": ordre,
    }


def arrondir(valeur, type_valeur):
    if not isinstance(valeur, (int, float)) or isinstance(valeur, bool):
        return valeur
    return round(valeur, 2) if type_valeur == "POURCENTAGE" else round(valeur)


def evaluer_regles(regles, valeurs, codes_connus, anomalies):
    """Applique les règles de l'institution aux résultats du calcul."""
    declenchees = []
    for regle in regles:
        try:
            arbre, references = analyser_condition(regle["condition"])
        except FormuleInvalide as erreur:
            anomalies.append({
                "code": regle.get("code", ""),
                "type": "REGLE_INVALIDE",
                "message": f"{regle.get('nom', 'Règle')} : {erreur}",
            })
            continue

        inconnues = references - set(valeurs) - codes_connus
        if inconnues:
            anomalies.append({
                "code": regle.get("code", ""),
                "type": "REGLE_INVALIDE",
                "message": f"{regle.get('nom', 'Règle')} : rubrique(s) inconnue(s) — {', '.join(sorted(inconnues))}.",
            })
            continue

        if evaluer(arbre, valeurs):
            declenchees.append({
                "code": regle.get("code", ""),
                "nom": regle.get("nom", ""),
                "resultat": regle.get("resultat", "POINT_ATTENTION"),
                "message": regle.get("message", ""),
                "condition": regle["condition"],
            })
    return declenchees


def executer_cadre(cadre, valeurs_saisies, contexte=None):
    """Exécute un objet CadreAnalyse et renvoie le résultat avec son snapshot."""
    definition = cadre.definition()
    regles = cadre.definition_regles()
    resultat = executer(definition, valeurs_saisies, regles, contexte)
    resultat["cadre"] = {
        "code": cadre.code,
        "nom": cadre.nom,
        "version": cadre.version,
        "reference": cadre.reference,
        "statut": cadre.statut,
    }
    resultat["snapshot"] = construire_snapshot(cadre, definition, regles, valeurs_saisies, contexte)
    return resultat


def construire_snapshot(cadre, definition, regles, valeurs_saisies, contexte=None):
    """Photographie complète de ce qui a produit une analyse.

    On enregistre la définition et les règles telles qu'elles étaient au moment
    du calcul, pas seulement une référence vers le cadre. Une analyse doit
    rester rejouable même si le cadre est dupliqué, republié ou supprimé.
    """
    return {
        "cadre": {"code": cadre.code, "nom": cadre.nom, "version": cadre.version},
        "definition": definition,
        "regles": regles,
        "valeurs_saisies": dict(valeurs_saisies),
        "contexte": dict(contexte or {}),
    }


def rejouer(snapshot):
    """Recalcule une analyse à partir de son seul snapshot."""
    return executer(
        snapshot["definition"],
        snapshot["valeurs_saisies"],
        snapshot["regles"],
        snapshot.get("contexte"),
    )
