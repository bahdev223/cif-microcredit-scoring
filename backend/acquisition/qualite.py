"""Contrôle qualité d'un lot, dimension par dimension.

Un pourcentage global unique ne dit rien d'actionnable : 88 % ne indique ni
quoi corriger, ni si le lot est utilisable. Le rapport expose donc six
dimensions séparées, et distingue trois natures de résultat :

    erreur bloquante   le lot ne peut pas être intégré en l'état
    avertissement      le lot est intégrable, mais quelque chose mérite un œil
    non vérifiable     la plateforme ne peut pas se prononcer

La dernière catégorie est la plus importante à afficher honnêtement.
L'exactitude — la valeur correspond-elle à la réalité ? — ne se contrôle pas
depuis un fichier : seule une visite ou un recoupement externe le permet.
"""

from datetime import date, datetime

FORMATS_DATE = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d")
SEUIL_ACTUALITE_JOURS = 400


def lire_date(valeur):
    for format_ in FORMATS_DATE:
        try:
            return datetime.strptime(str(valeur).strip()[:10], format_).date()
        except (ValueError, TypeError):
            continue
    return None


def est_nombre(valeur):
    try:
        float(str(valeur).replace(" ", "").replace(",", "."))
        return True
    except (ValueError, AttributeError):
        return False


def dimension(code, libelle, question, constat, anomalies=0, statut="ok", verifiable=True):
    return {
        "code": code,
        "libelle": libelle,
        "question": question,
        "constat": constat,
        "anomalies": anomalies,
        "statut": statut,
        "verifiable": verifiable,
    }


def evaluer(tables, champs_attendus, date_reference=None):
    """Produit le rapport qualité d'un lot déjà normalisé.

    `tables` associe un nom de table à ses lignes ; `champs_attendus` donne,
    par table, les champs obligatoires du référentiel.
    """
    date_reference = date_reference or date.today()
    anomalies, erreurs, avertissements = [], [], []

    completude = controler_completude(tables, champs_attendus, anomalies, erreurs, avertissements)
    unicite = controler_unicite(tables, anomalies, erreurs)
    validite = controler_validite(tables, anomalies, avertissements)
    coherence = controler_coherence(tables, anomalies, erreurs)
    actualite = controler_actualite(tables, date_reference, avertissements)

    exactitude = dimension(
        "exactitude", "Exactitude",
        "la valeur correspond-elle à la réalité ?",
        "Non vérifiable depuis un fichier. Seuls une visite, une pièce justificative "
        "ou un recoupement externe permettent de se prononcer.",
        statut="non_verifiable", verifiable=False,
    )

    return {
        "dimensions": [completude, actualite, unicite, validite, coherence, exactitude],
        "erreurs": erreurs,
        "avertissements": avertissements,
        "anomalies": anomalies[:200],
        "total_lignes": sum(len(lignes) for lignes in tables.values()),
        "integrable": not erreurs,
    }


def controler_completude(tables, champs_attendus, anomalies, erreurs, avertissements):
    cellules_vides = 0
    cellules_totales = 0
    for nom, lignes in tables.items():
        obligatoires = champs_attendus.get(nom, ())
        for numero, ligne in enumerate(lignes, start=2):
            for champ in obligatoires:
                cellules_totales += 1
                if not str(ligne.get(champ, "")).strip():
                    cellules_vides += 1
                    anomalies.append({"fichier": nom, "ligne": numero, "dimension": "completude",
                                      "type": "Champ obligatoire vide", "detail": champ})
    if cellules_vides:
        erreurs.append(f"{cellules_vides} champ(s) obligatoire(s) non renseigné(s).")

    facultatifs_vides = sum(
        1 for lignes in tables.values() for ligne in lignes
        for valeur in ligne.values() if not str(valeur).strip()
    )
    if facultatifs_vides:
        avertissements.append(f"{facultatifs_vides} valeur(s) absente(s) au total, champs facultatifs compris.")

    taux = 100 * (1 - cellules_vides / cellules_totales) if cellules_totales else 100
    return dimension(
        "completude", "Complétude", "les champs nécessaires sont-ils renseignés ?",
        f"{taux:.1f} % des champs obligatoires sont renseignés.",
        anomalies=cellules_vides, statut="erreur" if cellules_vides else "ok",
    )


def controler_unicite(tables, anomalies, erreurs):
    doublons = 0
    for nom, lignes in tables.items():
        if not lignes:
            continue
        cle = next((champ for champ in lignes[0] if champ.startswith("identifiant_")), None)
        if not cle:
            continue
        vus = set()
        for numero, ligne in enumerate(lignes, start=2):
            valeur = ligne.get(cle, "")
            if valeur and valeur in vus:
                doublons += 1
                anomalies.append({"fichier": nom, "ligne": numero, "dimension": "unicite",
                                  "type": "Identifiant en double", "detail": f"{cle} = {valeur}"})
            vus.add(valeur)
    if doublons:
        erreurs.append(f"{doublons} identifiant(s) apparaissent plusieurs fois.")
    return dimension(
        "unicite", "Unicité", "les identifiants censés être uniques le sont-ils ?",
        "Aucun doublon d'identifiant." if not doublons else f"{doublons} identifiant(s) en double.",
        anomalies=doublons, statut="erreur" if doublons else "ok",
    )


def controler_validite(tables, anomalies, avertissements):
    invalides = 0
    for nom, lignes in tables.items():
        for numero, ligne in enumerate(lignes, start=2):
            for champ, valeur in ligne.items():
                texte = str(valeur).strip()
                if not texte:
                    continue
                if champ.startswith("date_") and lire_date(texte) is None:
                    invalides += 1
                    anomalies.append({"fichier": nom, "ligne": numero, "dimension": "validite",
                                      "type": "Date illisible", "detail": f"{champ} = {texte}"})
                elif champ.startswith(("montant_", "duree_", "numero", "anciennete")) and not est_nombre(texte):
                    invalides += 1
                    anomalies.append({"fichier": nom, "ligne": numero, "dimension": "validite",
                                      "type": "Valeur non numérique", "detail": f"{champ} = {texte}"})
    if invalides:
        avertissements.append(f"{invalides} valeur(s) au format inattendu.")
    return dimension(
        "validite", "Validité", "le format, le type et le domaine sont-ils acceptables ?",
        "Formats conformes." if not invalides else f"{invalides} valeur(s) au format inattendu.",
        anomalies=invalides, statut="avertissement" if invalides else "ok",
    )


def controler_coherence(tables, anomalies, erreurs):
    """Relations entre tables et chronologie des dates."""
    relations = (
        ("activites", "identifiant_client", "clients", "identifiant_client"),
        ("demandes_credit", "identifiant_client", "clients", "identifiant_client"),
        ("credits", "identifiant_demande", "demandes_credit", "identifiant_demande"),
        ("echeances", "identifiant_credit", "credits", "identifiant_credit"),
        ("paiements", "identifiant_credit", "credits", "identifiant_credit"),
    )
    incoherences = 0
    for enfant, cle_enfant, parent, cle_parent in relations:
        if enfant not in tables or parent not in tables:
            continue
        connus = {ligne.get(cle_parent) for ligne in tables[parent]}
        for numero, ligne in enumerate(tables[enfant], start=2):
            valeur = ligne.get(cle_enfant)
            if valeur and valeur not in connus:
                incoherences += 1
                anomalies.append({"fichier": enfant, "ligne": numero, "dimension": "coherence",
                                  "type": "Rattachement introuvable",
                                  "detail": f"{cle_enfant} = {valeur} absent de {parent}"})

    decaissements = {
        ligne.get("identifiant_credit"): lire_date(ligne.get("date_decaissement"))
        for ligne in tables.get("credits", [])
    }
    for nom, champ in (("paiements", "date_paiement"), ("echeances", "date_exigible")):
        for numero, ligne in enumerate(tables.get(nom, []), start=2):
            moment = lire_date(ligne.get(champ))
            decaissement = decaissements.get(ligne.get("identifiant_credit"))
            if moment and decaissement and moment < decaissement:
                incoherences += 1
                anomalies.append({"fichier": nom, "ligne": numero, "dimension": "coherence",
                                  "type": "Chronologie impossible",
                                  "detail": f"{champ} antérieur au décaissement du crédit"})

    if incoherences:
        erreurs.append(f"{incoherences} incohérence(s) de rattachement ou de chronologie.")
    return dimension(
        "coherence", "Cohérence", "les relations et les dates sont-elles compatibles ?",
        "Relations et chronologie cohérentes." if not incoherences
        else f"{incoherences} incohérence(s) relevée(s).",
        anomalies=incoherences, statut="erreur" if incoherences else "ok",
    )


def controler_actualite(tables, date_reference, avertissements):
    dates = [
        moment
        for nom, champ in (("paiements", "date_paiement"), ("echeances", "date_exigible"),
                           ("credits", "date_decaissement"))
        for ligne in tables.get(nom, [])
        if (moment := lire_date(ligne.get(champ)))
    ]
    if not dates:
        return dimension(
            "actualite", "Actualité", "les données sont-elles assez récentes pour l'usage ?",
            "Aucune date exploitable : l'actualité du lot ne peut pas être appréciée.",
            statut="non_verifiable", verifiable=False,
        )

    plus_recente = max(dates)
    anciennete = (date_reference - plus_recente).days
    depassee = anciennete > SEUIL_ACTUALITE_JOURS
    if depassee:
        avertissements.append(
            f"La donnée la plus récente date du {plus_recente.isoformat()}, soit {anciennete} jours.")
    return dimension(
        "actualite", "Actualité", "les données sont-elles assez récentes pour l'usage ?",
        f"Donnée la plus récente : {plus_recente.isoformat()} ({anciennete} jours).",
        statut="avertissement" if depassee else "ok",
    )
