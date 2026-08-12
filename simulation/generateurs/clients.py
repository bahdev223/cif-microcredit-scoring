"""Génération déterministe des profils clients synthétiques."""

from datetime import date, timedelta


PRENOMS = ("Fatou", "Ibrahim", "Awa", "Moussa", "Mariam", "Oumar", "Binta", "Mamadou", "Aminata", "Seydou")
NOMS = ("Traore", "Konate", "Diallo", "Coulibaly", "Diakite", "Sissoko", "Keita", "Toure")


def generer_clients(nombre_clients, agences, secteurs, date_debut, aleatoire):
    """Retourne les lignes visibles et les paramètres internes du simulateur.

    Le risque latent n'est jamais écrit dans les CSV. Il sert uniquement à introduire
    de la variabilité dans le monde fictif.
    """
    lignes, profils_internes = [], {}
    for numero in range(1, nombre_clients + 1):
        identifiant = f"CLT-{numero:06d}"
        date_entree = date_debut - timedelta(days=aleatoire.randint(0, 5 * 365))
        secteur = aleatoire.choice(secteurs)
        profil = aleatoire.choice(("nouveau", "regulier", "saisonnier", "fragile"))
        lignes.append({
            "identifiant_client": identifiant,
            "identifiant_agence": aleatoire.choice(agences)["identifiant_agence"],
            "secteur_activite": secteur,
            "date_entree": date_entree.isoformat(),
            "profil_synthetique": profil,
        })
        profils_internes[identifiant] = {
            "nom": f"{aleatoire.choice(PRENOMS)} {aleatoire.choice(NOMS)}",
            "risque_latent": aleatoire.betavariate(2.2, 5.5),
            "stabilite_activite": aleatoire.uniform(0.55, 1.0),
            "profil": profil,
        }
    return lignes, profils_internes
