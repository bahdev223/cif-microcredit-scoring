"""Analyse préliminaire d'un dossier de demande.

Cette analyse n'est pas un score de risque. Elle présente, dans cet ordre :

1. la capacité financière, une simple soustraction que l'agent peut refaire
   de tête et contester ligne par ligne ;
2. le comportement de remboursement observé dans l'institution ;
3. la complétude du dossier, c'est-à-dire ce qui manque pour décider ;
4. et seulement à la fin, des indicateurs expérimentaux issus de règles
   pédagogiques, clairement identifiés comme tels.

Aucun modèle statistique n'a été validé sur les données d'une institution
réelle. L'application ne décide jamais : elle prépare la décision.
"""

from credits.rapprochement import rapprocher_credit

CHAMPS_DOSSIER = (
    ("recettes_activite", "Recettes de l'activité"),
    ("charges_activite", "Charges de l'activité"),
    ("charges_menage", "Charges du ménage"),
    ("anciennete_activite_mois", "Ancienneté de l'activité"),
    ("objet_credit", "Objet du financement"),
)


def analyser_dossier(demande, date_observation):
    client = demande.client
    return {
        "capacite": analyser_capacite(demande),
        "historique": analyser_historique(client, date_observation),
        "qualite_dossier": analyser_qualite_dossier(demande),
    }


def analyser_capacite(demande):
    """Ce que le client encaisse, ce qu'il dépense, ce qu'il lui reste.

    La marge est comparée à l'échéance estimée. Le rapprochement des deux est
    présenté comme un constat, jamais comme une décision.
    """
    lignes = [
        {"libelle": "Recettes de l'activité", "montant": demande.recettes_activite, "sens": "credit"},
        {"libelle": "Autres revenus du ménage", "montant": demande.autres_revenus_menage, "sens": "credit"},
        {"libelle": "Charges de l'activité", "montant": demande.charges_activite, "sens": "debit"},
        {"libelle": "Charges du ménage", "montant": demande.charges_menage, "sens": "debit"},
        {"libelle": "Engagements existants", "montant": demande.mensualite_dette_existante, "sens": "debit"},
    ]
    marge = demande.marge_estimee
    echeance = demande.echeance_estimee
    renseigne = any(ligne["montant"] for ligne in lignes)

    alerte = ""
    if not renseigne:
        alerte = "Aucun montant n'a été renseigné : la capacité de remboursement ne peut pas être appréciée."
    elif marge <= 0:
        alerte = "Les charges déclarées absorbent la totalité des recettes."
    elif echeance > marge:
        alerte = "L'échéance estimée dépasse la marge estimée."

    return {
        "lignes": lignes,
        "marge_estimee": marge,
        "echeance_estimee": echeance,
        "ecart": marge - echeance,
        "renseigne": renseigne,
        "alerte": alerte,
        "note_methode": "Échéance estimée hors intérêts et frais. La formule de l'institution doit remplacer ce calcul.",
    }


def analyser_historique(client, date_observation):
    """Comportement de remboursement déjà observé pour ce client."""
    credits = client.credits_importes.prefetch_related("echeances", "paiements").all()
    rapprochements = [rapprocher_credit(credit, date_observation) for credit in credits]

    if not rapprochements:
        return {
            "sans_historique": True,
            "message": "Aucun crédit antérieur enregistré pour ce client dans l'institution.",
        }

    return {
        "sans_historique": False,
        "nombre_credits": len(rapprochements),
        "nombre_soldes": sum(1 for r in rapprochements if r["statut"].startswith("SOLDE")),
        "nombre_en_cours": sum(1 for r in rapprochements if r["statut"] in ("EN_COURS", "EN_RETARD")),
        "nombre_avec_retard": sum(1 for r in rapprochements if r["jours_retard_max"] > 0),
        "jours_retard_max": max(r["jours_retard_max"] for r in rapprochements),
        "echeances_en_retard": sum(r["nombre_echeances_en_retard"] for r in rapprochements),
        "reste_du_total": sum(r["reste_du"] for r in rapprochements),
    }


def analyser_qualite_dossier(demande):
    """Ce qui est renseigné et ce qui manque, sans jugement de valeur."""
    controles = []
    for champ, libelle in CHAMPS_DOSSIER:
        valeur = getattr(demande, champ)
        controles.append({"libelle": libelle, "present": bool(valeur)})

    controles.append({"libelle": "Produit de crédit", "present": demande.produit_id is not None})
    controles.append({"libelle": "Historique interne", "present": demande.client.credits_importes.exists()})

    presents = sum(1 for controle in controles if controle["present"])
    return {
        "controles": controles,
        "renseignes": presents,
        "total": len(controles),
        "completude": round(100 * presents / len(controles)),
    }
