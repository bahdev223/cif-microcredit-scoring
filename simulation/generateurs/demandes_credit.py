"""Génération des demandes et décisions simulées, distinctes des remboursements."""

from datetime import timedelta


def generer_demandes(clients, profils_internes, resumes_activites, agents, produits, date_debut, date_fin, aleatoire):
    lignes, metadonnees = [], {}
    duree_jours = (date_fin - date_debut).days
    numero = 1
    for client in clients:
        identifiant_client = client["identifiant_client"]
        nombre_demandes = aleatoire.choices((0, 1, 2, 3, 4), weights=(8, 30, 35, 20, 7))[0]
        for _ in range(nombre_demandes):
            produit = aleatoire.choice(produits)
            date_demande = date_debut + timedelta(days=aleatoire.randint(30, max(31, duree_jours - 30)))
            montant = aleatoire.randint(produit["montant_min"], produit["montant_max"])
            duree = aleatoire.randint(produit["duree_min_mois"], produit["duree_max_mois"])
            marge = resumes_activites[identifiant_client]["marge_mensuelle"]
            echeance = montant / duree
            dossier_incomplet = aleatoire.random() < 0.06
            statut = "ACCEPTEE" if not dossier_incomplet and marge >= echeance * aleatoire.uniform(0.8, 1.25) else "REFUSEE"
            identifiant_demande = f"DMD-{numero:07d}"
            lignes.append({
                "identifiant_demande": identifiant_demande,
                "identifiant_client": identifiant_client,
                "identifiant_agent": aleatoire.choice(agents)["identifiant_agent"],
                "identifiant_produit": produit["identifiant_produit"],
                "date_demande": date_demande.isoformat(),
                "montant_demande": montant,
                "duree_mois": duree,
                "statut": statut,
            })
            metadonnees[identifiant_demande] = {"probabilite_incident": min(0.85, max(0.02, 0.08 + profils_internes[identifiant_client]["risque_latent"] * 0.42 + (resumes_activites[identifiant_client]["variabilite"] - 1) * 0.10 + aleatoire.uniform(-0.08, 0.08)))}
            numero += 1
    return lignes, metadonnees
