"""Niveau de confiance de l'analyse.

Un système utile doit savoir dire ce qu'il ne sait pas. Cette couche ne juge
pas le client : elle juge l'analyse elle-même. Deux dossiers identiques dont
l'un est complet et l'autre à moitié vide ne méritent pas la même confiance,
même s'ils produisent les mêmes chiffres.

Le cas du client sans historique est traité explicitement. Un nouveau client
n'est pas un bon client par défaut, ni un mauvais : c'est un client dont le
comportement de remboursement n'est pas observable. L'analyse le dit et
énumère ce sur quoi elle repose alors.
"""

PONDERATION_COMPLETUDE = 0.6
PONDERATION_MOTEURS = 0.4


def evaluer_confiance(moteurs, qualite_dossier, variables):
    evaluables = [moteur for moteur in moteurs if moteur["evaluable"]]
    part_moteurs = len(evaluables) / len(moteurs) if moteurs else 0
    part_completude = qualite_dossier["completude"] / 100

    niveau = round(100 * (PONDERATION_COMPLETUDE * part_completude + PONDERATION_MOTEURS * part_moteurs))

    if niveau >= 80:
        libelle, consequence = "Élevée", "Analyse exploitable en l'état."
    elif niveau >= 55:
        libelle, consequence = "Moyenne", "Analyse utilisable avec réserves."
    else:
        libelle, consequence = "Réduite", "Analyse insuffisante pour fonder une décision sans compléments."

    appuis, reserves = [], []
    for moteur in moteurs:
        if moteur["evaluable"]:
            appuis.append(moteur["libelle"])
        else:
            reserves.append(moteur["message"])

    for controle in qualite_dossier["controles"]:
        if not controle["present"]:
            reserves.append(f"{controle['libelle']} : information absente.")
    if variables["capacite_financiere"]["engagements"]:
        reserves.append("Endettement hors institution connu uniquement par déclaration.")

    return {
        "niveau": niveau,
        "libelle": libelle,
        "consequence": consequence,
        "appuis": appuis,
        "reserves": reserves,
        "moteurs_evaluables": len(evaluables),
        "moteurs_total": len(moteurs),
        "premiere_demande": not variables["comportement"]["historique_disponible"],
    }


def situation_premiere_demande(variables):
    """Bloc affiché lorsque le client n'a aucun historique interne."""
    if variables["comportement"]["historique_disponible"]:
        return None

    appuis = []
    if variables["capacite_financiere"]["renseignee"]:
        appuis.append("la situation économique déclarée")
    if variables["activite"]["anciennete_mois"]:
        appuis.append("l'ancienneté de l'activité")
    if variables["capacite_financiere"]["engagements"]:
        appuis.append("les engagements déclarés")
    appuis.append("les informations du dossier")

    return {
        "titre": "Première demande",
        "explication": (
            "Aucun crédit antérieur n'est enregistré pour ce client. "
            "Le comportement de remboursement ne peut donc pas être évalué."
        ),
        "appuis": appuis,
        "consequence": "Niveau de confiance réduit : l'analyse ne repose sur aucun antécédent observé.",
    }
