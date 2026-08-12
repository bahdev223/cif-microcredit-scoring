"""Simulation probabiliste des paiements et incidents."""

from datetime import date, timedelta


def generer_remboursements(echeances, metadonnees_credits, aleatoire):
    lignes, numero = [], 1
    for echeance in echeances:
        probabilite = metadonnees_credits[echeance["identifiant_credit"]]["probabilite_incident"]
        tirage = aleatoire.random()
        if tirage < probabilite * 0.12:
            montant_paye, jours_retard = 0, aleatoire.randint(90, 180)
        elif tirage < probabilite:
            montant_paye, jours_retard = echeance["montant_du"], aleatoire.randint(1, 45)
        else:
            montant_paye, jours_retard = echeance["montant_du"], 0
        date_paiement = date.fromisoformat(echeance["date_exigible"]) + timedelta(days=jours_retard)
        lignes.append({
            "identifiant_paiement": f"PMT-{numero:09d}",
            "identifiant_echeance": echeance["identifiant_echeance"],
            "date_paiement": date_paiement.isoformat(),
            "montant_paye": montant_paye,
            "jours_retard": jours_retard,
        })
        numero += 1
    return lignes
