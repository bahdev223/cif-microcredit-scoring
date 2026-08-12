"""Couche 0, étapes 2 à 5 : agences, agents, produits et secteurs.

Le décor se construit avant la population. Une agence doit exister avant qu'un
client lui soit rattaché, un agent doit être en fonction avant d'instruire un
dossier, un produit doit être lancé avant d'être demandé.
"""

from datetime import date

from .aleatoire import borner, flux
from .calendrier import ajouter_jours

PRENOMS = (
    "Fatoumata", "Ibrahim", "Awa", "Moussa", "Mariam", "Oumar", "Binta", "Mamadou",
    "Aminata", "Seydou", "Kadidia", "Bakary", "Salimata", "Adama", "Rokia", "Modibo",
)
NOMS = (
    "Traore", "Konate", "Diallo", "Coulibaly", "Diakite", "Sissoko", "Keita",
    "Toure", "Cisse", "Sangare", "Dembele", "Maiga",
)

LIBELLES_AGENCE = (
    "Agence centrale", "Agence du marché", "Agence nord", "Agence sud",
    "Agence est", "Agence ouest", "Agence de la gare", "Agence du fleuve",
    "Agence des artisans", "Agence de la route", "Agence du plateau",
)

# Répartition des zones d'agence autour de la zone dominante de l'institution.
# Une institution rurale garde toujours une ou deux agences urbaines : c'est
# cette hétérogénéité interne qui rend les comparaisons intéressantes.
ZONES_PAR_DOMINANTE = {
    "urbaine": ("urbaine", "urbaine", "urbaine", "semi_urbaine"),
    "semi_urbaine": ("semi_urbaine", "semi_urbaine", "urbaine", "rurale"),
    "rurale": ("rurale", "rurale", "rurale", "semi_urbaine", "urbaine"),
    "mixte": ("urbaine", "semi_urbaine", "rurale", "semi_urbaine"),
}


def dimensionner(profil_latent, nombre_clients_effectif):
    """Adapte la taille du décor au nombre de clients réellement générés.

    En mode échantillon, garder 8 agences pour 100 clients n'aurait aucun sens :
    on met à l'échelle, en gardant un minimum qui préserve l'hétérogénéité.
    """
    echelle = nombre_clients_effectif / profil_latent["nombre_clients_cible"]
    agences = borner(round(profil_latent["nombre_agences"] * echelle), 2, profil_latent["nombre_agences"])
    agents = borner(
        round(nombre_clients_effectif / profil_latent["clients_par_agent_cible"]),
        3,
        max(3, round(profil_latent["nombre_clients_cible"] / profil_latent["clients_par_agent_cible"])),
    )
    return int(agences), int(agents)


def generer_agences(institution, profil_latent, nombre_agences, graine, debut_du_monde, fin_du_monde,
                    premier_numero=1):
    agrement = date.fromisoformat(institution["date_agrement"])
    zones = ZONES_PAR_DOMINANTE[institution["zone_dominante"]]
    lignes = []

    for rang in range(1, nombre_agences + 1):
        identifiant = f"AGE-{premier_numero + rang - 1:03d}"
        aleatoire = flux(graine, "agence", institution["identifiant_institution"], rang)

        # La première agence ouvre avec l'institution. Les suivantes s'ajoutent
        # au fil du temps, et 15 % d'entre elles ouvrent pendant la simulation.
        if rang == 1:
            ouverture = agrement
        elif aleatoire.random() < 0.15:
            ouverture = ajouter_jours(debut_du_monde, aleatoire.randint(0, 1400))
        else:
            jours_disponibles = (debut_du_monde - agrement).days
            ouverture = ajouter_jours(agrement, aleatoire.randint(0, max(1, jours_disponibles)))

        fermeture = ""
        if aleatoire.random() < 0.02 and ouverture < debut_du_monde:
            fermeture = ajouter_jours(debut_du_monde, aleatoire.randint(200, 1700))
            fermeture = min(fermeture, fin_du_monde).isoformat()

        lignes.append({
            "identifiant_agence": identifiant,
            "identifiant_institution": institution["identifiant_institution"],
            "libelle_agence": LIBELLES_AGENCE[(rang - 1) % len(LIBELLES_AGENCE)],
            "zone": zones[(rang - 1) % len(zones)],
            "date_ouverture": ouverture.isoformat(),
            "date_fermeture": fermeture,
        })
    return lignes


def generer_agents_credit(institution, profil_latent, agences, nombre_agents, graine, debut_du_monde, fin_du_monde,
                          premier_numero=1):
    """Retourne les agents observables et leurs paramètres cachés.

    La sévérité de l'agent est latente : deux dossiers identiques instruits par
    deux agents différents ne reçoivent pas la même réponse, et c'est
    exactement la source d'hétérogénéité que la reject inference doit affronter.
    """
    observables, latents = [], []
    for rang in range(1, nombre_agents + 1):
        identifiant = f"AGT-{premier_numero + rang - 1:04d}"
        aleatoire = flux(graine, "agent", institution["identifiant_institution"], rang)
        agence = agences[(rang - 1) % len(agences)]
        ouverture_agence = date.fromisoformat(agence["date_ouverture"])

        plus_tot = max(ouverture_agence, date(debut_du_monde.year - 8, 1, 1))
        entree = ajouter_jours(plus_tot, aleatoire.randint(0, max(1, (fin_du_monde - plus_tot).days - 180)))

        sortie = ""
        annees_possibles = max(0, (fin_du_monde - entree).days / 365.25)
        if aleatoire.random() < 1 - (1 - profil_latent["rotation_annuelle_agents"]) ** annees_possibles:
            sortie = ajouter_jours(entree, aleatoire.randint(400, max(401, (fin_du_monde - entree).days)))
            sortie = min(sortie, fin_du_monde).isoformat()

        observables.append({
            "identifiant_agent": identifiant,
            "identifiant_institution": institution["identifiant_institution"],
            "identifiant_agence": agence["identifiant_agence"],
            "nom_agent": f"{PRENOMS[(rang * 7) % len(PRENOMS)]} {NOMS[(rang * 5) % len(NOMS)]}",
            "date_entree_fonction": entree.isoformat(),
            "date_sortie_fonction": sortie,
        })
        latents.append({
            "identifiant_agent": identifiant,
            "identifiant_institution": institution["identifiant_institution"],
            "severite": f"{borner(aleatoire.betavariate(4, 4) + (profil_latent['severite_octroi'] - 0.55), 0.05, 0.95):.4f}",
            "qualite_saisie": f"{aleatoire.betavariate(5, 2):.4f}",
        })
    return observables, latents


def generer_produits(configuration_produits):
    lignes = []
    for rang, produit in enumerate(configuration_produits["produits"], 1):
        lignes.append({
            "identifiant_produit": f"PRO-{rang:03d}",
            "code_produit": produit["code"],
            "libelle_produit": produit["libelle"],
            "montant_min": produit["montant_min"],
            "montant_max": produit["montant_max"],
            "duree_min_mois": produit["duree_min_mois"],
            "duree_max_mois": produit["duree_max_mois"],
            "periodicite": produit["periodicite"],
            "type_amortissement": produit["type_amortissement"],
            "differe_max_mois": produit["differe_max_mois"],
            "secteurs_cibles": "|".join(produit["secteurs_cibles"]),
            "date_lancement": produit["date_lancement"],
        })
    return lignes


def generer_secteurs(configuration_secteurs):
    """Sépare le référentiel observable de ses paramètres économiques cachés."""
    observables, latents = [], []
    for rang, secteur in enumerate(configuration_secteurs["secteurs"], 1):
        observables.append({
            "identifiant_secteur": f"SEC-{rang:02d}",
            "code_secteur": secteur["code"],
            "libelle_secteur": secteur["libelle"],
            "cycle_activite": secteur["cycle"],
        })
        parametres = secteur["parametres"]
        latents.append({
            "code_secteur": secteur["code"],
            "recettes_mensuelles_medianes": parametres["recettes_mensuelles_medianes"],
            "marge_structurelle": f"{parametres['marge_structurelle']:.4f}",
            "amplitude_saisonniere": f"{parametres['amplitude_saisonniere']:.4f}",
            "mois_pic": parametres["mois_pic"],
            "volatilite_base": f"{parametres['volatilite_base']:.4f}",
        })
    return observables, latents
