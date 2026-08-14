"""Complétude du dossier de demande.

Ce module ne dit pas si un dossier est bon : il dit ce qui est renseigné et
ce qui manque. C'est la matière du niveau de confiance, et le premier
écran que corrigera un agent de crédit.
"""

CHAMPS_DOSSIER = (
    ("recettes_activite", "Recettes de l'activité"),
    ("charges_activite", "Charges de l'activité"),
    ("charges_menage", "Charges du ménage"),
    ("anciennete_activite_mois", "Ancienneté de l'activité"),
    ("objet_credit", "Objet du financement"),
)



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
