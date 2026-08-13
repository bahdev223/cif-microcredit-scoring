"""Rapprochement entre les échéances attendues et les paiements reçus.

Une échéance dit ce qui devait arriver, un paiement dit ce qui est réellement
arrivé. Tout le suivi d'un crédit vit dans l'écart entre les deux : reste dû,
retard, régularisation, crédit soldé.

La règle d'imputation appliquée ici est la plus simple qui soit : chaque
versement rembourse la plus ancienne échéance non soldée. Elle est volontairement
explicite et isolée dans ce module, parce que c'est exactement le genre de règle
qu'un agent de crédit doit pouvoir corriger : « chez nous, on impute d'abord les
pénalités », « un versement ne solde jamais deux échéances », etc.

Aucun seuil réglementaire n'est appliqué. Les retards sont comptés en jours et
présentés par tranches d'ancienneté, sans qualifier un crédit de « douteux » ni
de « compromis » : ces définitions appartiennent à l'institution.
"""

from datetime import date

from django.db.models import Max

TRANCHES_RETARD = ((1, 30), (31, 90), (91, None))


def date_observation_portefeuille():
    """Date jusqu'à laquelle les livres de l'institution sont à jour.

    C'est la date du dernier paiement enregistré. Deux raisons : les données de
    démonstration sont historiques, donc les comparer à la date du jour
    afficherait un portefeuille entièrement échu ; et un échéancier court par
    nature dans le futur, si bien qu'un maximum pris sur toutes les dates
    rendrait impossible la notion même d'échéance à venir.

    L'interface affiche toujours cette date : l'agent doit savoir à quelle date
    il regarde son portefeuille.
    """
    from .models import EcheanceImportee, PaiementImporte

    dernier_paiement = PaiementImporte.objects.aggregate(valeur=Max("date_paiement"))["valeur"]
    if dernier_paiement:
        return dernier_paiement
    derniere_echeance = EcheanceImportee.objects.aggregate(valeur=Max("date_exigible"))["valeur"]
    return derniere_echeance or date.today()


def rapprocher_credit(credit, date_observation):
    """Impute les paiements d'un crédit sur ses échéances, la plus ancienne d'abord."""
    echeances = sorted(credit.echeances.all(), key=lambda e: (e.date_exigible or date.max, e.numero))
    paiements = sorted(credit.paiements.all(), key=lambda p: p.date_paiement or date.max)

    restes = {echeance.id: echeance.montant_du for echeance in echeances}
    dates_couverture = {}
    for paiement in paiements:
        disponible = paiement.montant_paye
        for echeance in echeances:
            if disponible <= 0:
                break
            if restes[echeance.id] <= 0:
                continue
            impute = min(disponible, restes[echeance.id])
            restes[echeance.id] -= impute
            disponible -= impute
            if restes[echeance.id] == 0:
                dates_couverture[echeance.id] = paiement.date_paiement

    lignes, jours_retard_max, nombre_en_retard = [], 0, 0
    for echeance in echeances:
        reste = restes[echeance.id]
        exigible = echeance.date_exigible
        date_couverture = dates_couverture.get(echeance.id)
        if not exigible:
            jours_retard = 0
        elif reste > 0:
            # Échéance encore ouverte : le retard court jusqu'à aujourd'hui.
            jours_retard = max(0, (date_observation - exigible).days)
        else:
            jours_retard = max(0, (date_couverture - exigible).days) if date_couverture else 0

        en_retard = reste > 0 and exigible is not None and exigible < date_observation
        if en_retard:
            nombre_en_retard += 1
        jours_retard_max = max(jours_retard_max, jours_retard)
        lignes.append({
            "numero": echeance.numero,
            "date_exigible": exigible.isoformat() if exigible else "",
            "montant_du": echeance.montant_du,
            "montant_couvert": echeance.montant_du - reste,
            "reste_du": reste,
            "date_couverture": date_couverture.isoformat() if date_couverture else "",
            "jours_retard": jours_retard,
            "en_retard": en_retard,
        })

    total_du = sum(echeance.montant_du for echeance in echeances)
    total_paye = sum(paiement.montant_paye for paiement in paiements)
    reste_du = max(0, total_du - total_paye)
    if not echeances:
        statut = "SANS_ECHEANCIER"
    elif reste_du == 0:
        statut = "SOLDE_AVEC_RETARD" if jours_retard_max > 0 else "SOLDE"
    elif nombre_en_retard:
        statut = "EN_RETARD"
    else:
        statut = "EN_COURS"

    return {
        "identifiant": credit.identifiant_source,
        "montant_decaisse": credit.montant_decaisse,
        "duree_mois": credit.duree_mois,
        "date_decaissement": credit.date_decaissement.isoformat() if credit.date_decaissement else "",
        "statut": statut,
        "total_du": total_du,
        "total_paye": total_paye,
        "reste_du": reste_du,
        "jours_retard_max": jours_retard_max,
        "nombre_echeances": len(echeances),
        "nombre_echeances_en_retard": nombre_en_retard,
        "nombre_paiements": len(paiements),
        "echeances": lignes,
        "paiements": [{
            "date": paiement.date_paiement.isoformat() if paiement.date_paiement else "",
            "montant": paiement.montant_paye,
            "canal": paiement.canal,
        } for paiement in paiements],
    }


def tranche_retard(jours):
    for debut, fin in TRANCHES_RETARD:
        if jours >= debut and (fin is None or jours <= fin):
            return f"{debut}-{fin} j" if fin else f"plus de {debut - 1} j"
    return ""
