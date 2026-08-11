def construire_caracteristiques(client, demande_credit):
    echeance = demande_credit.echeance_estimee
    capacite_remboursement = client.revenu_mensuel - client.charges_mensuelles
    return {
        "capacite_remboursement": capacite_remboursement,
        "echeance": echeance,
        "ratio_capacite": capacite_remboursement / echeance if echeance else 0,
        "anciennete_activite_mois": client.anciennete_activite_mois,
        "nombre_retards": client.nombre_retards,
        "regularite_tontine": client.regularite_tontine,
    }
