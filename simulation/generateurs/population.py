"""Couche 1, étapes 6 et 7 : les clients et leurs activités économiques.

Un client et son activité sont deux choses différentes. Le client entre en
relation avec une institution ; l'activité produit des recettes. Un client peut
exercer deux activités, et une activité peut s'arrêter sans que la relation
s'arrête.

Chaque client reçoit une personnalité financière — discipline, vulnérabilité,
appétence au crédit — qui n'est écrite que dans verite/. C'est elle qui
produira son comportement, et c'est elle que le modèle devra redécouvrir.
"""

from datetime import date

from .aleatoire import beta_bornee, borner, flux, log_normale, tirage_pondere
from .calendrier import ajouter_jours, ajouter_mois, ecart_en_mois

# Bibliothèque des scénarios de comportement. Ils décrivent des personnalités
# économiques exclusives : un client en a un et un seul. Les paiements
# partiels, les régularisations ou les enchaînements de crédits ne sont pas ici
# — ce sont des conséquences, elles doivent émerger du moteur, pas être tirées.
SCENARIOS = {
    "S01": {"libelle": "Excellent payeur", "part": 0.08, "discipline": (0.90, 0.99), "volatilite": (0.05, 0.15)},
    "S02": {"libelle": "Payeur normal", "part": 0.28, "discipline": (0.70, 0.90)},
    "S03": {"libelle": "Retards occasionnels", "part": 0.12, "discipline": (0.55, 0.70)},
    "S04": {"libelle": "Retards frequents", "part": 0.08, "discipline": (0.35, 0.55)},
    "S05": {"libelle": "Defaut precoce", "part": 0.02, "discipline": (0.10, 0.35), "vulnerabilite": (0.60, 0.95)},
    "S06": {"libelle": "Defaut apres plusieurs bons credits", "part": 0.03, "discipline": (0.75, 0.95), "choc_tardif": True},
    "S07": {"libelle": "Nouveau client sans historique", "part": 0.07, "entree_recente": True},
    "S08": {"libelle": "Fortes recettes faible marge", "part": 0.04, "facteur_niveau": (1.8, 3.0), "marge": (0.03, 0.10)},
    "S09": {"libelle": "Faibles recettes forte marge", "part": 0.05, "facteur_niveau": (0.3, 0.6), "marge": (0.35, 0.50)},
    "S10": {"libelle": "Endettement croissant", "part": 0.04, "endettement_croissant": True},
    "S11": {"libelle": "Activite tres saisonniere", "part": 0.05, "amplitude": (0.45, 0.70)},
    "S12": {"libelle": "Revenus tres volatils", "part": 0.05, "volatilite": (0.40, 0.60)},
    "S13": {"libelle": "Amelioration progressive", "part": 0.04, "croissance": (0.15, 0.35)},
    "S14": {"libelle": "Degradation progressive", "part": 0.05, "croissance": (-0.25, -0.10)},
}

LIBELLES_ACTIVITE = {
    "COMMERCE": ("Vente de céréales", "Boutique de quartier", "Vente de tissus", "Commerce de condiments"),
    "AGRICULTURE": ("Culture maraîchère", "Production de mil", "Riziculture", "Culture d'arachide"),
    "ELEVAGE": ("Élevage de volaille", "Embouche bovine", "Élevage de petits ruminants", "Production laitière"),
    "ARTISANAT": ("Couture", "Menuiserie", "Forge", "Teinture de tissus"),
    "RESTAURATION": ("Vente de repas", "Restaurant de rue", "Préparation de jus", "Vente de beignets"),
    "TRANSPORT": ("Transport de personnes", "Livraison de marchandises", "Taxi moto", "Location de tricycle"),
    "SERVICES": ("Coiffure", "Réparation de téléphones", "Cabine de communication", "Secrétariat public"),
    "PETITE_PRODUCTION": ("Transformation de céréales", "Fabrication de savon", "Production de jus", "Séchage de fruits"),
}


def _parts_scenarios():
    return {code: details["part"] for code, details in SCENARIOS.items()}


def _valeur_ou_defaut(aleatoire, scenario, cle, valeur_par_defaut):
    """Applique la contrainte du scénario si elle existe, sinon garde le tirage."""
    borne = SCENARIOS[scenario].get(cle)
    if borne is None:
        return valeur_par_defaut
    return aleatoire.uniform(*borne)


def _calendrier_arrivees(nombre_clients, profil_latent, debut_du_monde, fin_du_monde):
    """Répartit les entrées en relation entre le stock initial et les années.

    Le rythme suit la croissance propre à l'institution : une institution jeune
    et conquérante recrute tard, donc ses clients ont des historiques courts.
    """
    stock_initial = round(nombre_clients * profil_latent["part_clients_stock_initial"])
    annees = list(range(debut_du_monde.year, fin_du_monde.year + 1))
    poids = [(1 + profil_latent["croissance_annuelle_portefeuille"]) ** rang for rang in range(len(annees))]
    total_poids = sum(poids)

    restants = nombre_clients - stock_initial
    repartition = [round(restants * part / total_poids) for part in poids]
    repartition[-1] += restants - sum(repartition)
    return stock_initial, dict(zip(annees, repartition))


def generer_clients(institution, profil_latent, mix_sectoriel, agences, nombre_clients,
                    graine, debut_du_monde, fin_du_monde, premier_numero=1):
    identifiant_institution = institution["identifiant_institution"]
    ouverture_la_plus_ancienne = min(date.fromisoformat(agence["date_ouverture"]) for agence in agences)
    stock_initial, arrivees = _calendrier_arrivees(nombre_clients, profil_latent, debut_du_monde, fin_du_monde)

    # File des dates d'entrée, construite avant les clients pour rester stable.
    file_dates = []
    for rang in range(stock_initial):
        aleatoire = flux(graine, "entree_stock", identifiant_institution, rang)
        file_dates.append(ajouter_jours(debut_du_monde, -aleatoire.randint(30, 7 * 365)))
    for annee, nombre in arrivees.items():
        for rang in range(nombre):
            aleatoire = flux(graine, "entree_annee", identifiant_institution, annee, rang)
            file_dates.append(date(annee, 1, 1) + (date(annee, 12, 31) - date(annee, 1, 1)) * aleatoire.random())
    file_dates.sort()

    observables, latents = [], []
    for rang, date_entree in enumerate(file_dates):
        numero = premier_numero + rang
        identifiant = f"CLT-{numero:06d}"
        aleatoire = flux(graine, "client", identifiant)
        scenario = tirage_pondere(aleatoire, _parts_scenarios())

        # Un nouveau client sans historique entre forcément tard dans le monde.
        if SCENARIOS[scenario].get("entree_recente"):
            date_entree = ajouter_jours(fin_du_monde, -aleatoire.randint(30, 365))

        # Un client ne peut pas entrer en relation avant qu'une agence existe.
        # Chez une institution jeune, cela raccourcit mécaniquement le stock
        # initial : c'est le bon comportement, pas une limite à contourner.
        date_entree = max(date_entree, ouverture_la_plus_ancienne)
        ouvertes = [
            agence for agence in agences
            if date.fromisoformat(agence["date_ouverture"]) <= date_entree
        ]
        en_activite = [
            agence for agence in ouvertes
            if not agence["date_fermeture"] or date.fromisoformat(agence["date_fermeture"]) > date_entree
        ]
        agence = aleatoire.choice(en_activite or ouvertes)

        discipline = _valeur_ou_defaut(
            aleatoire, scenario, "discipline",
            beta_bornee(aleatoire, 6, 2, profil_latent["decalage_discipline"]),
        )
        vulnerabilite = _valeur_ou_defaut(aleatoire, scenario, "vulnerabilite", aleatoire.betavariate(2, 4))
        appetence = aleatoire.betavariate(2, 3)

        possede_epargne = aleatoire.random() < borner(0.45 + 0.30 * discipline, 0.05, 0.95)
        epargne = round(log_normale(aleatoire, 45000, 0.9) / 500) * 500 if possede_epargne else ""

        date_sortie = ""
        propension_sortie = borner(aleatoire.gauss(0.005, 0.002), 0.001, 0.02)
        mois_presents = max(1, ecart_en_mois(date_entree, fin_du_monde))
        if aleatoire.random() < 1 - (1 - propension_sortie) ** mois_presents:
            sortie = ajouter_mois(date_entree, aleatoire.randint(12, max(13, mois_presents)))
            if sortie < fin_du_monde:
                date_sortie = sortie.isoformat()

        observables.append({
            "identifiant_client": identifiant,
            "identifiant_institution": identifiant_institution,
            "identifiant_agence": agence["identifiant_agence"],
            "date_entree_relation": date_entree.isoformat(),
            "date_sortie_relation": date_sortie,
            "code_secteur_principal": tirage_pondere(aleatoire, mix_sectoriel),
            "anciennete_activite_mois_a_entree": int(borner(round(log_normale(aleatoire, 48, 0.8)), 0, 360)),
            "possede_compte_epargne": 1 if possede_epargne else 0,
            "montant_epargne_a_entree": epargne,
        })
        latents.append({
            "identifiant_client": identifiant,
            "identifiant_institution": identifiant_institution,
            "scenario_comportement": scenario,
            "code_personnage": "",
            "discipline_paiement": f"{discipline:.4f}",
            "vulnerabilite_choc": f"{vulnerabilite:.4f}",
            "appetence_credit": f"{appetence:.4f}",
            "propension_sortie": f"{propension_sortie:.4f}",
            "coussin_epargne_initial": epargne if epargne != "" else 0,
            "choc_tardif": 1 if SCENARIOS[scenario].get("choc_tardif") else 0,
            "endettement_croissant": 1 if SCENARIOS[scenario].get("endettement_croissant") else 0,
        })
    return observables, latents


def generer_activites(clients, profils_latents, parametres_secteurs, mix_sectoriel,
                      profil_latent_institution, graine, fin_du_monde, premier_numero=1):
    """Retourne les activités observables et leurs paramètres économiques cachés."""
    secteurs = {ligne["code_secteur"]: ligne for ligne in parametres_secteurs}
    scenarios = {ligne["identifiant_client"]: ligne["scenario_comportement"] for ligne in profils_latents}

    observables, latents = [], []
    numero = premier_numero - 1
    for client in clients:
        identifiant_client = client["identifiant_client"]
        scenario = scenarios[identifiant_client]
        aleatoire = flux(graine, "activites", identifiant_client)
        date_entree = date.fromisoformat(client["date_entree_relation"])
        debut_activite = ajouter_mois(date_entree, -client["anciennete_activite_mois_a_entree"])

        codes = [client["code_secteur_principal"]]
        if aleatoire.random() < 0.30:
            secondaire = tirage_pondere(aleatoire, mix_sectoriel)
            if secondaire != codes[0]:
                codes.append(secondaire)

        for position, code_secteur in enumerate(codes):
            numero += 1
            identifiant = f"ACT-{numero:06d}"
            parametres = secteurs[code_secteur]
            principale = position == 0

            fin_activite = ""
            if not principale and aleatoire.random() < 0.08:
                fin = ajouter_mois(date_entree, aleatoire.randint(6, 48))
                if fin < fin_du_monde:
                    fin_activite = fin.isoformat()

            mediane = float(parametres["recettes_mensuelles_medianes"])
            facteur = _valeur_ou_defaut(aleatoire, scenario, "facteur_niveau", 1.0)
            niveau = log_normale(aleatoire, mediane, 0.75) * facteur
            if not principale:
                niveau *= aleatoire.uniform(0.25, 0.60)

            marge = _valeur_ou_defaut(
                aleatoire, scenario, "marge",
                borner(aleatoire.gauss(float(parametres["marge_structurelle"]), 0.05), 0.02, 0.55),
            )
            volatilite = _valeur_ou_defaut(
                aleatoire, scenario, "volatilite",
                borner(
                    float(parametres["volatilite_base"]) + profil_latent_institution["decalage_volatilite"]
                    + aleatoire.gauss(0, 0.04),
                    0.05, 0.60,
                ),
            )
            amplitude = _valeur_ou_defaut(
                aleatoire, scenario, "amplitude",
                borner(float(parametres["amplitude_saisonniere"]) + aleatoire.gauss(0, 0.05), 0.0, 0.70),
            )
            croissance = _valeur_ou_defaut(
                aleatoire, scenario, "croissance", borner(aleatoire.gauss(0.03, 0.10), -0.25, 0.35)
            )

            observables.append({
                "identifiant_activite": identifiant,
                "identifiant_client": identifiant_client,
                "identifiant_institution": client["identifiant_institution"],
                "code_secteur": code_secteur,
                "libelle_activite": aleatoire.choice(LIBELLES_ACTIVITE[code_secteur]),
                "est_activite_principale": 1 if principale else 0,
                "date_debut_activite": debut_activite.isoformat(),
                "date_fin_activite": fin_activite,
            })
            latents.append({
                "identifiant_activite": identifiant,
                "identifiant_client": identifiant_client,
                "recettes_initiales": int(round(niveau)),
                "marge_structurelle": f"{marge:.4f}",
                "croissance_annuelle": f"{croissance:.4f}",
                "volatilite_recettes": f"{volatilite:.4f}",
                "amplitude_saisonniere": f"{amplitude:.4f}",
                "mois_pic": int(borner(int(parametres["mois_pic"]) + aleatoire.randint(-1, 1), 1, 12)),
            })
    return observables, latents
