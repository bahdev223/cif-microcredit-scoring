"""Correspondance entre les colonnes de l'institution et notre référentiel.

Deux décisions sont prises ici, et toutes deux sont des propositions :

1. **à quelle table correspond ce fichier ?** — par le nom du fichier, et
   surtout par ce que ses colonnes reconnaissent ;
2. **à quel champ correspond cette colonne ?** — par égalité, par synonyme,
   puis par ressemblance.

Rien n'est jamais décidé automatiquement de façon définitive. Chaque
proposition porte son degré de certitude et son motif, et un humain la valide
ou la corrige avant tout import. Une colonne non reconnue n'est pas une
erreur : elle est signalée, et l'agent choisit de l'ignorer ou de l'associer.

La normalisation est volontairement brutale — accents retirés, ponctuation
ramenée à rien, majuscules — parce que `Montant Décaissé`, `MONTANT_DECAISSE`
et `montant.decaisse` désignent la même chose.
"""

import unicodedata
from difflib import SequenceMatcher

from .referentiel import ORDRE_TABLES, TABLES

SEUIL_RESSEMBLANCE = 0.82
SEUIL_TABLE = 0.34


def normaliser(texte):
    sans_accent = unicodedata.normalize("NFKD", str(texte or ""))
    sans_accent = "".join(caractere for caractere in sans_accent if not unicodedata.combining(caractere))
    retenus = [caractere.lower() if caractere.isalnum() else " " for caractere in sans_accent]
    return "_".join("".join(retenus).split())


def _index_synonymes(table):
    """Écriture normalisée → code du champ, pour une table donnée."""
    index = {}
    for code, champ in TABLES[table]["champs"].items():
        index.setdefault(normaliser(code), code)
        for synonyme in champ["synonymes"]:
            index.setdefault(normaliser(synonyme), code)
    return index


def proposer_champ(entete, table, deja_pris=()):
    """Propose un champ du référentiel pour une colonne, avec son motif."""
    normalisee = normaliser(entete)
    index = _index_synonymes(table)

    code = index.get(normalisee)
    if code and code not in deja_pris:
        motif = "identique" if normalisee == normaliser(code) else "synonyme connu"
        return {"champ": code, "certitude": "certaine", "motif": motif}

    meilleur, score_max = None, 0.0
    for ecriture, candidat in index.items():
        if candidat in deja_pris:
            continue
        score = SequenceMatcher(None, normalisee, ecriture).ratio()
        if score > score_max:
            meilleur, score_max = candidat, score

    if meilleur and score_max >= SEUIL_RESSEMBLANCE:
        return {"champ": meilleur, "certitude": "probable", "motif": f"écriture proche ({round(score_max * 100)} %)"}
    return {"champ": "", "certitude": "inconnue", "motif": "aucune correspondance trouvée"}


def proposer_table(nom_fichier, entetes):
    """Devine la table visée par un fichier, sans se fier au seul nom."""
    normalise = normaliser(nom_fichier)
    scores = {}

    for table in ORDRE_TABLES:
        index = _index_synonymes(table)
        reconnues = sum(1 for entete in entetes if normaliser(entete) in index)
        obligatoires = [code for code, champ in TABLES[table]["champs"].items() if champ["obligatoire"]]
        couverture_obligatoires = sum(
            1 for code in obligatoires
            if any(index.get(normaliser(entete)) == code for entete in entetes)
        ) / (len(obligatoires) or 1)

        score = 0.55 * (reconnues / (len(entetes) or 1)) + 0.45 * couverture_obligatoires
        if normaliser(table) in normalise:
            score += 0.35
        scores[table] = score

    table, score = max(scores.items(), key=lambda couple: couple[1])
    if score < SEUIL_TABLE:
        return {"table": "", "certitude": "inconnue", "score": round(score, 2)}
    certitude = "certaine" if score >= 0.7 else "probable"
    return {"table": table, "certitude": certitude, "score": round(score, 2)}


def proposer_correspondance(nom_fichier, entetes):
    """Proposition complète pour un fichier : table visée et colonnes."""
    table_proposee = proposer_table(nom_fichier, entetes)
    table = table_proposee["table"]

    colonnes, deja_pris = [], set()
    for entete in entetes:
        proposition = proposer_champ(entete, table, deja_pris) if table else {
            "champ": "", "certitude": "inconnue", "motif": "table du fichier non identifiée"}
        if proposition["champ"]:
            deja_pris.add(proposition["champ"])
        colonnes.append({"colonne": entete, **proposition})

    manquants = []
    if table:
        associes = {colonne["champ"] for colonne in colonnes if colonne["champ"]}
        manquants = [{
            "champ": code,
            "libelle": champ["libelle"],
            "obligatoire": champ["obligatoire"],
        } for code, champ in TABLES[table]["champs"].items() if code not in associes]

    return {
        "fichier": nom_fichier,
        "table": table,
        "table_certitude": table_proposee["certitude"],
        "colonnes": colonnes,
        "champs_non_associes": manquants,
        "colonnes_non_reconnues": [colonne["colonne"] for colonne in colonnes if not colonne["champ"]],
    }


def appliquer(correspondance, lignes):
    """Traduit les lignes de l'institution vers le référentiel interne.

    Les colonnes non associées ne sont pas jetées : elles sont conservées à
    part, pour que l'agent puisse constater ce qui n'a pas été repris et que
    la source reste inspectable.
    """
    associations = {
        colonne["colonne"]: colonne["champ"]
        for colonne in correspondance["colonnes"] if colonne.get("champ")
    }

    normalisees, ecartees = [], []
    for ligne in lignes:
        traduite, reste = {}, {}
        for entete, valeur in ligne.items():
            champ = associations.get(entete)
            if champ:
                traduite[champ] = valeur
            elif str(valeur).strip():
                reste[entete] = valeur
        normalisees.append(traduite)
        ecartees.append(reste)

    return normalisees, ecartees
