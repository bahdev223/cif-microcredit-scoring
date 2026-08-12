"""Couche 0, étape 1 : génération des institutions fictives.

Cette étape ne tire rien au hasard. Les cinq institutions sont entièrement
décrites dans configuration/institutions.yaml : le générateur se contente de
les valider, de leur attribuer un identifiant stable et de séparer ce qui est
observable de ce qui reste caché au modèle de scoring.

Sorties :
    brutes/01_institutions.csv              ce que le modèle a le droit de lire
    verite/01_profils_institutions.csv      paramètres internes du simulateur
    verite/01_mix_sectoriel.csv             composition sectorielle visée
    verite/01_mix_produits.csv              orientation produit visée
"""

TOLERANCE_SOMME = 1e-9

CHAMPS_OBSERVABLES = (
    "identifiant_institution",
    "libelle_institution",
    "code_profil_portefeuille",
    "zone_dominante",
    "specialisation_principale",
    "date_agrement",
    "pays_de_demonstration",
    "est_fictive",
)

CHAMPS_LATENTS = (
    "identifiant_institution",
    "nombre_clients_cible",
    "nombre_agences",
    "clients_par_agent_cible",
    "part_clients_stock_initial",
    "croissance_annuelle_portefeuille",
    "severite_octroi",
    "taux_acceptation_cible",
    "taux_defaut_experimental_cible",
    "multiplicateur_montant",
    "decalage_discipline",
    "decalage_volatilite",
    "sensibilite_macro",
    "facteur_qualite_donnees",
    "rotation_annuelle_agents",
)

ZONES_ADMISES = ("urbaine", "semi_urbaine", "rurale", "mixte")


def _verifier_somme(poids, identifiant, nom_du_bloc):
    total = sum(poids.values())
    if abs(total - 1.0) > TOLERANCE_SOMME:
        raise ValueError(
            f"{identifiant} : le {nom_du_bloc} doit sommer à 1.00, il somme à {total:.6f}"
        )
    for code, valeur in poids.items():
        if valeur < 0:
            raise ValueError(f"{identifiant} : poids négatif pour {code} dans le {nom_du_bloc}")


def _verifier_coherence(institution, identifiant, latent, mix_sectoriel):
    if institution["zone_dominante"] not in ZONES_ADMISES:
        raise ValueError(
            f"{identifiant} : zone_dominante inconnue « {institution['zone_dominante']} »"
        )

    specialisation = institution["specialisation_principale"]
    if specialisation != "DIVERSIFIE":
        if specialisation not in mix_sectoriel:
            raise ValueError(
                f"{identifiant} : la spécialisation {specialisation} est absente du mix sectoriel"
            )
        secteur_dominant = max(mix_sectoriel, key=mix_sectoriel.get)
        if secteur_dominant != specialisation:
            raise ValueError(
                f"{identifiant} : la spécialisation annoncée est {specialisation} mais le mix"
                f" est dominé par {secteur_dominant}"
            )

    if not 0 < latent["taux_acceptation_cible"] < 1:
        raise ValueError(f"{identifiant} : taux_acceptation_cible hors de ]0, 1[")
    if not 0 < latent["taux_defaut_experimental_cible"] < 1:
        raise ValueError(f"{identifiant} : taux_defaut_experimental_cible hors de ]0, 1[")
    if latent["nombre_agences"] < 1:
        raise ValueError(f"{identifiant} : une institution a besoin d'au moins une agence")
    if latent["clients_par_agent_cible"] < 1:
        raise ValueError(f"{identifiant} : clients_par_agent_cible doit être positif")


def generer_institutions(configuration):
    """Retourne les quatre tables de la couche institutions.

    Le résultat est un dictionnaire de listes de lignes, prêt à être écrit en
    CSV. L'ordre des institutions est celui du fichier de configuration : il
    détermine les identifiants, donc il ne doit pas être modifié à la légère.
    """
    pays = configuration.get("pays_de_demonstration", "")
    observables, latents, lignes_secteurs, lignes_produits = [], [], [], []

    for rang, institution in enumerate(configuration["institutions"], 1):
        identifiant = f"INS-{rang:03d}"
        latent = institution["latent"]
        mix_sectoriel = institution["mix_sectoriel"]
        mix_produits = institution["mix_produits"]

        _verifier_somme(mix_sectoriel, identifiant, "mix sectoriel")
        _verifier_somme(mix_produits, identifiant, "mix produits")
        _verifier_coherence(institution, identifiant, latent, mix_sectoriel)

        observables.append({
            "identifiant_institution": identifiant,
            "libelle_institution": institution["libelle"],
            "code_profil_portefeuille": institution["code_profil_portefeuille"],
            "zone_dominante": institution["zone_dominante"],
            "specialisation_principale": institution["specialisation_principale"],
            "date_agrement": institution["date_agrement"],
            "pays_de_demonstration": pays,
            "est_fictive": 1,
        })

        ligne_latente = {"identifiant_institution": identifiant}
        for champ in CHAMPS_LATENTS[1:]:
            if champ not in latent:
                raise ValueError(f"{identifiant} : paramètre latent manquant « {champ} »")
            valeur = latent[champ]
            # Les effectifs restent entiers, les taux et coefficients s'écrivent
            # à quatre décimales comme le prévoit la convention du dictionnaire.
            ligne_latente[champ] = valeur if isinstance(valeur, int) else f"{valeur:.4f}"
        latents.append(ligne_latente)

        for code_secteur, poids in sorted(mix_sectoriel.items()):
            lignes_secteurs.append({
                "identifiant_institution": identifiant,
                "code_secteur": code_secteur,
                "poids_population": f"{poids:.4f}",
            })

        for code_produit, poids in sorted(mix_produits.items()):
            lignes_produits.append({
                "identifiant_institution": identifiant,
                "code_produit": code_produit,
                "poids_octroi": f"{poids:.4f}",
            })

    return {
        "observables": observables,
        "latents": latents,
        "mix_sectoriel": lignes_secteurs,
        "mix_produits": lignes_produits,
    }
