def construire_caracteristiques(client, demande_credit):
    """Caractéristiques utilisées par les règles expérimentales.

    On lit en priorité la situation relevée sur la demande elle-même : c'est
    celle dont l'agent disposait au moment d'instruire. La fiche client, qui a
    pu évoluer depuis, ne sert que de repli quand la demande n'a rien de saisi.
    """
    echeance = demande_credit.echeance_estimee

    if demande_credit.recettes_activite or demande_credit.charges_activite:
        capacite_remboursement = demande_credit.marge_estimee
        anciennete = demande_credit.anciennete_activite_mois or client.anciennete_activite_mois
    else:
        capacite_remboursement = (client.revenu_mensuel - client.charges_mensuelles
                                  - client.mensualite_dette_existante)
        anciennete = client.anciennete_activite_mois

    return {
        "capacite_remboursement": capacite_remboursement,
        "echeance": echeance,
        "ratio_capacite": capacite_remboursement / echeance if echeance else 0,
        "anciennete_activite_mois": anciennete,
        "nombre_retards": client.nombre_retards,
        "regularite_tontine": client.regularite_tontine,
    }
