"""Couche 1, étape 8 : le moteur économique du monde.

C'est ici que le monde se met à vivre. Chaque activité produit des recettes
mois après mois, sous l'effet de quatre forces : sa tendance de fond, son
cycle saisonnier, le contexte macroéconomique de son secteur, et les
événements qui lui tombent dessus. Le tout est bruité, avec de la mémoire :
un mauvais mois pèse sur le suivant.

Rien de tout cela n'est observable. L'institution ne voit que ce qu'un agent a
noté à quelques dates — ce sont les relevés d'activité, produits en fin de
module.
"""

import math
from datetime import date

from .aleatoire import borner, flux, log_normale
from .calendrier import (
    ajouter_mois,
    cle_mois,
    jour_dans_le_mois,
    mois_vers_couple,
    premier_jour_du_mois,
    suite_de_mois,
)

CORRELATION_BRUIT = 0.5  # mémoire du bruit d'un mois sur l'autre

EVENEMENTS_NEGATIFS = (
    "baisse_ventes", "mauvaise_recolte", "perte_stock",
    "fermeture_temporaire", "hausse_charges", "depense_exceptionnelle",
)
EVENEMENTS_POSITIFS = (
    "hausse_activite", "bonne_recolte", "nouveau_contrat",
    "elargissement_clientele", "nouvel_equipement", "desendettement",
)


def construire_contexte_macro(configuration, nom_scenario, debut_du_monde, fin_du_monde, codes_secteurs):
    """Déplie le scénario macroéconomique en une table mois x secteur."""
    scenario = configuration["scenarios"][nom_scenario]
    contexte = {
        (mois, code): {"indice_activite": 1.0, "indice_charges": 1.0, "choc_actif": ""}
        for mois in suite_de_mois(debut_du_monde, fin_du_monde)
        for code in codes_secteurs
    }

    for periode in scenario["periodes"]:
        secteurs = codes_secteurs if periode["secteurs"] == "tous" else periode["secteurs"]
        mois_periode = suite_de_mois(
            premier_jour_du_mois(periode["debut"]), premier_jour_du_mois(periode["fin"])
        )
        for mois in mois_periode:
            for code in secteurs:
                if (mois, code) not in contexte:
                    continue
                contexte[(mois, code)] = {
                    "indice_activite": periode["indice_activite"],
                    "indice_charges": periode["indice_charges"],
                    "choc_actif": periode["libelle"] if periode["indice_activite"] != 1.0 else "",
                }

    lignes = [
        {
            "mois": mois,
            "code_secteur": code,
            "indice_activite": f"{valeurs['indice_activite']:.4f}",
            "indice_charges": f"{valeurs['indice_charges']:.4f}",
            "choc_actif": valeurs["choc_actif"],
        }
        for (mois, code), valeurs in sorted(contexte.items())
    ]
    return contexte, lignes


def _fenetre_de_vie(client, activite, debut_du_monde, fin_du_monde):
    """Mois pendant lesquels une activité est réellement en marche."""
    debut = max(
        debut_du_monde,
        date.fromisoformat(client["date_entree_relation"]),
        date.fromisoformat(activite["date_debut_activite"]),
    )
    fins = [fin_du_monde]
    if client["date_sortie_relation"]:
        fins.append(date.fromisoformat(client["date_sortie_relation"]))
    if activite["date_fin_activite"]:
        fins.append(date.fromisoformat(activite["date_fin_activite"]))
    fin = min(fins)
    if fin < debut:
        return []
    return suite_de_mois(debut, fin)


def generer_evenements(clients, profils_latents, contexte_macro, graine, debut_du_monde, fin_du_monde):
    """Tire les chocs économiques individuels, positifs et négatifs.

    Le catalogue reste strictement économique : aucun événement de santé, de
    famille ou de deuil. Ces situations existent, mais dans un laboratoire de
    scoring elles finiraient par devenir des variables de décision.
    """
    latents = {ligne["identifiant_client"]: ligne for ligne in profils_latents}
    lignes, effets = [], {}
    numero = 0

    for client in clients:
        identifiant = client["identifiant_client"]
        profil = latents[identifiant]
        vulnerabilite = float(profil["vulnerabilite_choc"])
        aleatoire = flux(graine, "evenements", identifiant)

        debut = max(debut_du_monde, date.fromisoformat(client["date_entree_relation"]))
        fin = min(
            fin_du_monde,
            date.fromisoformat(client["date_sortie_relation"]) if client["date_sortie_relation"] else fin_du_monde,
        )
        if fin < debut:
            continue
        mois_de_vie = suite_de_mois(debut, fin)
        secteur = client["code_secteur_principal"]

        # Le client à choc tardif traverse plusieurs bons crédits avant de
        # rencontrer un accident majeur : on le place dans le dernier tiers.
        mois_choc_tardif = None
        if profil["choc_tardif"] == 1 and len(mois_de_vie) > 12:
            mois_choc_tardif = mois_de_vie[int(len(mois_de_vie) * aleatoire.uniform(0.60, 0.85))]

        for mois in mois_de_vie:
            sous_choc = bool(contexte_macro.get((mois, secteur), {}).get("choc_actif"))
            risque_negatif = 0.025 * (0.5 + vulnerabilite) * (1.8 if sous_choc else 1.0)
            forcer = mois == mois_choc_tardif

            if forcer or aleatoire.random() < risque_negatif:
                intensite = aleatoire.uniform(0.50, 0.80) if forcer else aleatoire.uniform(0.05, 0.60)
                duree = aleatoire.randint(6, 12) if forcer else aleatoire.randint(1, 8)
                numero += 1
                lignes.append({
                    "identifiant_evenement": f"EVT-{numero:06d}",
                    "identifiant_client": identifiant,
                    "identifiant_institution": client["identifiant_institution"],
                    "mois_debut": mois,
                    "duree_mois": duree,
                    "code_evenement": aleatoire.choice(EVENEMENTS_NEGATIFS),
                    "sens": "negatif",
                    "intensite": f"{intensite:.4f}",
                    "source": "macro" if sous_choc and not forcer else "idiosyncratique",
                })
                _appliquer_effet(effets, identifiant, mois, duree, 1.0 - intensite)

            elif aleatoire.random() < 0.020:
                intensite = aleatoire.uniform(0.05, 0.45)
                duree = aleatoire.randint(2, 10)
                numero += 1
                lignes.append({
                    "identifiant_evenement": f"EVT-{numero:06d}",
                    "identifiant_client": identifiant,
                    "identifiant_institution": client["identifiant_institution"],
                    "mois_debut": mois,
                    "duree_mois": duree,
                    "code_evenement": aleatoire.choice(EVENEMENTS_POSITIFS),
                    "sens": "positif",
                    "intensite": f"{intensite:.4f}",
                    "source": "idiosyncratique",
                })
                _appliquer_effet(effets, identifiant, mois, duree, 1.0 + intensite * 0.6)

    return lignes, effets


def _appliquer_effet(effets, identifiant_client, mois_debut, duree, facteur):
    jour = premier_jour_du_mois(mois_debut)
    for decalage in range(duree):
        cle = (identifiant_client, cle_mois(ajouter_mois(jour, decalage)))
        effets[cle] = effets.get(cle, 1.0) * facteur


def generer_situations_mensuelles(clients, activites, parametres_activites, contexte_macro,
                                  effets_evenements, profil_latent_institution, graine,
                                  debut_du_monde, fin_du_monde):
    """Produit la trajectoire économique réelle, mois par mois et activité par activité."""
    parametres = {ligne["identifiant_activite"]: ligne for ligne in parametres_activites}
    clients_par_identifiant = {ligne["identifiant_client"]: ligne for ligne in clients}
    sensibilite = profil_latent_institution["sensibilite_macro"]

    situations, par_activite = [], {}
    for activite in activites:
        client = clients_par_identifiant[activite["identifiant_client"]]
        mois_de_vie = _fenetre_de_vie(client, activite, debut_du_monde, fin_du_monde)
        if not mois_de_vie:
            continue

        reglages = parametres[activite["identifiant_activite"]]
        niveau = float(reglages["recettes_initiales"])
        croissance = float(reglages["croissance_annuelle"])
        volatilite = float(reglages["volatilite_recettes"])
        amplitude = float(reglages["amplitude_saisonniere"])
        mois_pic = int(reglages["mois_pic"])
        marge = float(reglages["marge_structurelle"])

        aleatoire = flux(graine, "situations", activite["identifiant_activite"])
        bruit = aleatoire.gauss(0, volatilite)
        innovation = volatilite * math.sqrt(1 - CORRELATION_BRUIT ** 2)

        for rang, mois in enumerate(mois_de_vie):
            _, numero_mois = mois_vers_couple(mois)
            saison = 1 + amplitude * math.cos(2 * math.pi * (numero_mois - mois_pic) / 12)
            macro = contexte_macro.get((mois, activite["code_secteur"]), {"indice_activite": 1.0, "indice_charges": 1.0})
            effet_macro = macro["indice_activite"] ** sensibilite
            effet_evenement = effets_evenements.get((activite["identifiant_client"], mois), 1.0)

            bruit = CORRELATION_BRUIT * bruit + aleatoire.gauss(0, innovation)
            tendance = (1 + croissance) ** (rang / 12)

            recettes = niveau * tendance * saison * effet_macro * effet_evenement * math.exp(bruit - volatilite ** 2 / 2)
            recettes = max(0.0, recettes)
            charges = recettes * (1 - marge) * macro["indice_charges"]

            ligne = {
                "identifiant_activite": activite["identifiant_activite"],
                "identifiant_client": activite["identifiant_client"],
                "identifiant_institution": activite["identifiant_institution"],
                "mois": mois,
                "recettes_reelles": int(round(recettes)),
                "charges_reelles": int(round(charges)),
                "revenu_net_reel": int(round(recettes - charges)),
                "indice_saison": f"{saison:.4f}",
                "effet_evenement": f"{effet_evenement:.4f}",
                "effet_macro": f"{effet_macro:.4f}",
            }
            situations.append(ligne)
            par_activite[(activite["identifiant_activite"], mois)] = ligne

    return situations, par_activite


def generer_capacite_mensuelle(clients, situations, graine, debut_du_monde, fin_du_monde):
    """Agrège les activités d'un client et en déduit sa capacité mensuelle.

    Cette capacité ignore volontairement les remboursements de crédit en cours :
    les échéances ne sont connues qu'à la couche 13. Le moteur de paiement
    tiendra son propre solde, alimenté par cette capacité.
    """
    # Index par client plutôt que balayage : à 50 000 clients et 2,4 millions
    # de situations, une recherche linéaire par client rendrait la couche
    # inutilisable.
    revenus = {}
    for ligne in situations:
        revenus.setdefault(ligne["identifiant_client"], {})
        cle = ligne["mois"]
        revenus[ligne["identifiant_client"]][cle] = (
            revenus[ligne["identifiant_client"]].get(cle, 0) + ligne["revenu_net_reel"]
        )

    lignes, capacites = [], {}
    for client in clients:
        identifiant = client["identifiant_client"]
        aleatoire = flux(graine, "menage", identifiant)
        part_menage = borner(aleatoire.gauss(0.55, 0.12), 0.25, 0.85)
        autres_revenus_base = log_normale(aleatoire, 60000, 1.0) if aleatoire.random() < 0.65 else 0.0

        revenus_du_client = revenus.get(identifiant, {})
        coussin = float(client["montant_epargne_a_entree"] or 0)

        for mois in sorted(revenus_du_client):
            revenu = revenus_du_client[mois]
            autres_revenus = autres_revenus_base * aleatoire.uniform(0.7, 1.3) if autres_revenus_base else 0.0
            charges_menage = max(0.0, revenu) * part_menage
            capacite = revenu + autres_revenus - charges_menage
            coussin = max(0.0, coussin + capacite * 0.25)

            lignes.append({
                "identifiant_client": identifiant,
                "identifiant_institution": client["identifiant_institution"],
                "mois": mois,
                "revenu_net_activites": int(round(revenu)),
                "autres_revenus_menage": int(round(autres_revenus)),
                "charges_menage": int(round(charges_menage)),
                "capacite_mensuelle": int(round(capacite)),
                "coussin_estime": int(round(coussin)),
            })
            capacites[(identifiant, mois)] = lignes[-1]
    return lignes, capacites


def preparer_dettes_externes(clients, profils_latents, graine):
    """Dette contractée hors de l'institution : l'angle mort classique du scoring.

    22 % des clients en portent une. Ceux du scénario « endettement croissant »
    la voient grossir d'année en année, ce qui n'apparaîtra dans les données que
    par la comparaison de deux relevés successifs.
    """
    latents = {ligne["identifiant_client"]: ligne for ligne in profils_latents}
    dettes = {}
    for client in clients:
        identifiant = client["identifiant_client"]
        aleatoire = flux(graine, "dette_externe", identifiant)
        croissante = latents[identifiant]["endettement_croissant"] == 1
        if not croissante and aleatoire.random() > 0.22:
            continue
        dettes[identifiant] = {
            "montant": log_normale(aleatoire, 35000, 0.8),
            "croissante": croissante,
            "depart": date.fromisoformat(client["date_entree_relation"]),
        }
    return dettes


def _dette_a_la_date(dettes, identifiant_client, jour):
    dette = dettes.get(identifiant_client)
    if dette is None:
        return ""
    annees = max(0.0, (jour - dette["depart"]).days / 365.25)
    facteur = (1.35 ** annees) if dette["croissante"] else 1.0
    return int(round(dette["montant"] * facteur / 500) * 500)


def generer_releves_de_base(clients, activites, situations_par_activite, capacites,
                            dettes, graine, debut_du_monde, fin_du_monde):
    """Relevés d'entrée en relation et visites de suivi.

    Les relevés d'instruction, eux, naissent avec les demandes de crédit : ils
    sont ajoutés par la couche 09.
    """
    activites_par_client = {}
    for activite in activites:
        activites_par_client.setdefault(activite["identifiant_client"], []).append(activite)

    releves = []
    for client in clients:
        identifiant = client["identifiant_client"]
        aleatoire = flux(graine, "releves", identifiant)
        entree = date.fromisoformat(client["date_entree_relation"])
        fin = min(
            fin_du_monde,
            date.fromisoformat(client["date_sortie_relation"]) if client["date_sortie_relation"] else fin_du_monde,
        )

        dates_releve = [max(entree, debut_du_monde)]
        mois_suivant = ajouter_mois(max(entree, debut_du_monde), 12)
        while mois_suivant < fin:
            if aleatoire.random() < 0.35:
                dates_releve.append(jour_dans_le_mois(aleatoire, cle_mois(mois_suivant)))
            mois_suivant = ajouter_mois(mois_suivant, 12)

        for position, jour in enumerate(dates_releve):
            origine = "entree_relation" if position == 0 else "visite_suivi"
            releves.extend(
                construire_releves(
                    client, activites_par_client.get(identifiant, []), situations_par_activite,
                    capacites, dettes, jour, origine, aleatoire,
                )
            )
    return releves


def construire_releves(client, activites, situations_par_activite, capacites, dettes, jour, origine, aleatoire):
    """Fabrique les lignes déclaratives observées à une date donnée.

    Un chiffre donné pour obtenir un crédit n'a pas la fiabilité d'un chiffre
    relevé en visite : le biais de déclaration est donc plus fort à
    l'instruction. Il existe dans la vraie vie, le modèle doit vivre avec.
    """
    mois = cle_mois(jour)
    biais_recettes = aleatoire.uniform(1.0, 1.25) if origine == "instruction_demande" else aleatoire.uniform(0.95, 1.08)
    biais_charges = aleatoire.uniform(0.80, 1.0) if origine == "instruction_demande" else aleatoire.uniform(0.95, 1.05)
    capacite = capacites.get((client["identifiant_client"], mois))

    lignes = []
    for activite in activites:
        situation = situations_par_activite.get((activite["identifiant_activite"], mois))
        if situation is None:
            continue
        stock = ""
        if activite["code_secteur"] in ("COMMERCE", "RESTAURATION", "PETITE_PRODUCTION"):
            stock = int(round(situation["recettes_reelles"] * aleatoire.uniform(0.4, 1.6)))

        lignes.append({
            "identifiant_releve": None,
            "identifiant_activite": activite["identifiant_activite"],
            "identifiant_client": client["identifiant_client"],
            "identifiant_institution": client["identifiant_institution"],
            "date_releve": jour.isoformat(),
            "origine_releve": origine,
            "recettes_mensuelles_declarees": int(round(situation["recettes_reelles"] * biais_recettes)),
            "charges_mensuelles_declarees": int(round(situation["charges_reelles"] * biais_charges)),
            "stock_estime": stock,
            "autres_revenus_menage": capacite["autres_revenus_menage"] if capacite else "",
            "charges_menage": capacite["charges_menage"] if capacite else "",
            "dette_externe_mensualite": _dette_a_la_date(dettes, client["identifiant_client"], jour),
        })
    return lignes
