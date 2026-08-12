"""Transformation des demandes acceptées en crédits et échéances."""

from datetime import date


def ajouter_mois(date_depart, nombre_mois):
    mois = date_depart.month - 1 + nombre_mois
    return date(date_depart.year + mois // 12, mois % 12 + 1, min(date_depart.day, 28))


def generer_credits(demandes, metadonnees_demandes):
    credits, echeances, metadonnees_credits = [], [], {}
    numero_credit, numero_echeance = 1, 1
    for demande in demandes:
        if demande["statut"] != "ACCEPTEE":
            continue
        identifiant_credit = f"CRD-{numero_credit:07d}"
        decaissement = date.fromisoformat(demande["date_demande"])
        echeance_mensuelle = round(demande["montant_demande"] / demande["duree_mois"])
        credits.append({
            "identifiant_credit": identifiant_credit,
            "identifiant_demande": demande["identifiant_demande"],
            "date_decaissement": decaissement.isoformat(),
            "montant_decaisse": demande["montant_demande"],
            "duree_mois": demande["duree_mois"],
            "echeance_mensuelle": echeance_mensuelle,
        })
        metadonnees_credits[identifiant_credit] = metadonnees_demandes[demande["identifiant_demande"]]
        for numero in range(1, demande["duree_mois"] + 1):
            echeances.append({
                "identifiant_echeance": f"ECH-{numero_echeance:08d}",
                "identifiant_credit": identifiant_credit,
                "numero": numero,
                "date_exigible": ajouter_mois(decaissement, numero).isoformat(),
                "montant_du": echeance_mensuelle,
            })
            numero_echeance += 1
        numero_credit += 1
    return credits, echeances, metadonnees_credits
