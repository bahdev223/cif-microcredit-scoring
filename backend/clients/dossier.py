"""Assemble le dossier complet d'un client pour la fiche du poste de travail.

La fiche client est le centre du prototype : c'est l'écran devant lequel un
agent de crédit doit pouvoir dire « oui, c'est mon travail » ou « non, chez nous
ça se passe autrement ». Elle rassemble donc tout ce que nous savons du client,
dans l'ordre où un professionnel le lit : qui il est, ce qu'il fait, ce qu'il a
emprunté, et comment il a remboursé.

Aucun indicateur n'est inventé ici. Chaque chiffre affiché vient d'une donnée
saisie ou importée, ou d'un calcul dont la règle est écrite dans le code.
"""

from credits.rapprochement import rapprocher_credit

LIBELLES_STATUT = {
    "SOLDE": "Soldé",
    "SOLDE_AVEC_RETARD": "Soldé avec retard",
    "EN_COURS": "En cours",
    "EN_RETARD": "En retard",
    "SANS_ECHEANCIER": "Sans échéancier",
}


def construire_dossier(client, date_observation):
    credits = list(client.credits_importes.prefetch_related("echeances", "paiements").all())
    rapprochements = sorted(
        (rapprocher_credit(credit, date_observation) for credit in credits),
        key=lambda r: r["date_decaissement"],
    )
    activites = list(client.activites_importees.all())
    demandes_importees = sorted(client.demandes_importees.all(), key=lambda d: d.date_demande or client.cree_le.date())
    demandes_en_cours = list(client.demandes_credit.order_by("cree_le"))

    return {
        "client": {
            "identifiant": client.id,
            "nom_complet": client.nom_complet,
            "identifiant_source": client.identifiant_source or "",
            "secteur_activite": client.secteur_activite,
            "anciennete_activite_mois": client.anciennete_activite_mois,
            "cree_le": client.cree_le.isoformat(),
        },
        "synthese": construire_synthese(client, rapprochements),
        "activites": [{
            "libelle": activite.libelle or activite.secteur,
            "secteur": activite.secteur,
            "est_principale": activite.est_principale,
            "date_debut": activite.date_debut.isoformat() if activite.date_debut else "",
        } for activite in activites],
        "historique_credit": rapprochements,
        "demandes_en_cours": [{
            "identifiant": demande.id,
            "montant_demande": demande.montant_demande,
            "duree_mois": demande.duree_mois,
            "niveau_risque": demande.niveau_risque,
            "decision_agent": demande.decision_agent,
            "cree_le": demande.cree_le.isoformat(),
        } for demande in demandes_en_cours],
        "chronologie": construire_chronologie(client, rapprochements, demandes_importees, demandes_en_cours),
    }


def construire_synthese(client, rapprochements):
    """Capacité déclarée et comportement de remboursement observé.

    La marge est une soustraction, pas un score : recettes moins charges moins
    engagements. Elle sert de point de départ à la discussion avec l'agent, qui
    corrigera la formule si son institution calcule autrement.
    """
    marge = client.revenu_mensuel - client.charges_mensuelles - client.mensualite_dette_existante
    soldes = [r for r in rapprochements if r["statut"].startswith("SOLDE")]
    return {
        "recettes_declarees": client.revenu_mensuel,
        "charges_declarees": client.charges_mensuelles,
        "engagements_existants": client.mensualite_dette_existante,
        "marge_estimee": marge,
        "nombre_credits": len(rapprochements),
        "nombre_credits_soldes": len(soldes),
        "nombre_credits_en_cours": sum(1 for r in rapprochements if r["statut"] in ("EN_COURS", "EN_RETARD")),
        "montant_total_emprunte": sum(r["montant_decaisse"] for r in rapprochements),
        "reste_du_total": sum(r["reste_du"] for r in rapprochements),
        "jours_retard_max": max((r["jours_retard_max"] for r in rapprochements), default=0),
        "nombre_echeances_en_retard": sum(r["nombre_echeances_en_retard"] for r in rapprochements),
        "retards_declares_a_la_saisie": client.nombre_retards,
    }


def construire_chronologie(client, rapprochements, demandes_importees, demandes_en_cours):
    """Suite d'événements datés, du plus ancien au plus récent."""
    evenements = [{
        "date": client.cree_le.date().isoformat(),
        "type": "adhesion",
        "libelle": "Entrée en relation",
        "detail": client.secteur_activite,
    }]

    for demande in demandes_importees:
        evenements.append({
            "date": demande.date_demande.isoformat() if demande.date_demande else "",
            "type": "demande",
            "libelle": f"Demande de {demande.montant:,} F".replace(",", " "),
            "detail": demande.objet or f"{demande.duree_mois} mois",
        })

    for credit in rapprochements:
        evenements.append({
            "date": credit["date_decaissement"],
            "type": "decaissement",
            "libelle": f"Crédit décaissé {credit['montant_decaisse']:,} F".replace(",", " "),
            "detail": f"{credit['duree_mois']} mois · {credit['identifiant']}",
        })

        if credit["nombre_paiements"]:
            dernier = credit["paiements"][-1]
            evenements.append({
                "date": dernier["date"],
                "type": "remboursement",
                "libelle": f"{credit['nombre_paiements']} remboursements reçus",
                "detail": f"{credit['total_paye']:,} F versés".replace(",", " "),
            })

        premier_retard = next((e for e in credit["echeances"] if e["jours_retard"] > 0), None)
        if premier_retard:
            evenements.append({
                "date": premier_retard["date_exigible"],
                "type": "retard",
                "libelle": f"Retard de {premier_retard['jours_retard']} jours",
                "detail": f"Échéance {premier_retard['numero']} · {credit['identifiant']}",
            })
            if premier_retard["date_couverture"]:
                evenements.append({
                    "date": premier_retard["date_couverture"],
                    "type": "regularisation",
                    "libelle": "Régularisation",
                    "detail": f"Échéance {premier_retard['numero']} soldée",
                })

        if credit["statut"].startswith("SOLDE") and credit["paiements"]:
            evenements.append({
                "date": credit["paiements"][-1]["date"],
                "type": "solde",
                "libelle": "Crédit soldé",
                "detail": credit["identifiant"],
            })

    for demande in demandes_en_cours:
        evenements.append({
            "date": demande.cree_le.date().isoformat(),
            "type": "demande_en_cours",
            "libelle": f"Nouvelle demande {demande.montant_demande:,} F".replace(",", " "),
            "detail": "En cours d'instruction",
        })

    return sorted((e for e in evenements if e["date"]), key=lambda e: e["date"])
