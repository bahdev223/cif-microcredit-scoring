"""Couches 2 et 3 : demandes, décisions, crédits, échéances, paiements, résultats.

Le cycle complet se déroule client par client, dans l'ordre du temps. Une
demande naît d'un besoin, une décision y répond, un crédit en découle, un
échéancier dit ce qui devait arriver et les paiements disent ce qui est
réellement arrivé. Le défaut n'est jamais tiré au sort : il est constaté à la
fin, à partir de la trajectoire observée.
"""

import math
from datetime import date

from .aleatoire import borner, flux, tirage_pondere
from .calendrier import ajouter_jours, ajouter_mois, cle_mois, ecart_en_mois, suite_de_mois
from .economie import construire_releves

SEUIL_DEFAUT_JOURS = 90
SEUIL_ABANDON_JOURS = 120
DUREES_PRIVILEGIEES = {3: 1, 6: 4, 9: 3, 12: 5, 18: 1, 24: 1}


def _sigmoide(valeur):
    return 1 / (1 + math.exp(-borner(valeur, -30, 30)))


def _agent_disponible(agents, agence, jour, aleatoire):
    candidats = [
        agent for agent in agents
        if agent["identifiant_agence"] == agence
        and date.fromisoformat(agent["date_entree_fonction"]) <= jour
        and (not agent["date_sortie_fonction"] or date.fromisoformat(agent["date_sortie_fonction"]) > jour)
    ]
    if not candidats:
        candidats = [
            agent for agent in agents
            if date.fromisoformat(agent["date_entree_fonction"]) <= jour
            and (not agent["date_sortie_fonction"] or date.fromisoformat(agent["date_sortie_fonction"]) > jour)
        ]
    return aleatoire.choice(candidats) if candidats else None


def _produit_eligible(produits, mix_produits, secteur, jour, aleatoire):
    poids = {}
    for produit in produits:
        if produit["code_produit"] not in mix_produits:
            continue
        if date.fromisoformat(produit["date_lancement"]) > jour:
            continue
        if secteur not in produit["secteurs_cibles"].split("|"):
            continue
        poids[produit["code_produit"]] = mix_produits[produit["code_produit"]]
    if not poids or sum(poids.values()) <= 0:
        return None
    code = tirage_pondere(aleatoire, poids)
    return next(produit for produit in produits if produit["code_produit"] == code)


def _echeancier(montant, duree, decaissement, differe):
    """Amortissement à capital constant, intérêts nuls tant que le taux n'est pas arrêté."""
    capital_unitaire = montant // duree
    lignes = []
    for numero in range(1, duree + 1):
        capital = capital_unitaire if numero < duree else montant - capital_unitaire * (duree - 1)
        lignes.append({
            "numero_echeance": numero,
            "date_exigible": ajouter_mois(decaissement, differe + numero),
            "montant_capital_du": capital,
            "montant_interet_du": 0,
            "montant_total_du": capital,
        })
    return lignes


def _simuler_paiements(echeances, discipline, capacites, identifiant_client, coussin_initial,
                       fin_du_monde, aleatoire, biais_paiement):
    """Fait vivre un échéancier et retourne les versements réellement effectués.

    Aucune règle du type « mauvais payeur donc défaut » : on simule un
    comportement mois par mois, sous contrainte de trésorerie, et le résultat
    se constate ensuite.
    """
    versements = []
    coussin = float(coussin_initial)
    dernier_versement = None

    for echeance in echeances:
        exigible = echeance["date_exigible"]
        if exigible > fin_du_monde:
            break

        capacite = capacites.get((identifiant_client, cle_mois(exigible)))
        disponible = max(0.0, (capacite["capacite_mensuelle"] if capacite else 0) + coussin)
        montant_du = echeance["montant_total_du"]
        ratio = disponible / montant_du if montant_du else 0.0

        # La discipline pèse plus lourd que l'aisance de trésorerie, et la
        # contribution du ratio sature vite : au-delà d'une fois et demie
        # l'échéance, avoir davantage d'argent ne rend pas plus ponctuel. Sans
        # cette hiérarchie, un client indiscipliné mais à l'aise paierait comme
        # un excellent payeur, et la personnalité latente ne laisserait aucune
        # trace apprenable dans les données.
        chance = _sigmoide(-2.2 + 4.2 * discipline + 1.0 * min(ratio, 1.5) + biais_paiement)
        tire = aleatoire.random()

        if tire < chance:
            jour = ajouter_jours(exigible, aleatoire.randint(-3, 4))
            if jour > fin_du_monde:
                break  # le versement aurait lieu après la fin du monde : non observé
            paye = montant_du
            versements.append((jour, paye, "complet"))
            dernier_versement = jour
            coussin = max(0.0, disponible - paye)
            continue

        # Le client n'a pas pu, ou pas voulu, payer normalement.
        if ratio > 0.45 and aleatoire.random() < 0.55:
            part = aleatoire.uniform(0.30, 0.80)
            premier = ajouter_jours(exigible, aleatoire.randint(0, 12))
            if premier > fin_du_monde:
                break
            paye = int(round(montant_du * part))
            versements.append((premier, paye, "partiel"))
            dernier_versement = premier
            coussin = max(0.0, disponible - paye)

            if aleatoire.random() < 0.70:
                complement = ajouter_jours(exigible, aleatoire.randint(15, 75))
                if complement <= fin_du_monde:
                    versements.append((complement, montant_du - paye, "complement"))
                    dernier_versement = complement
            continue

        retard = aleatoire.random()
        if retard < 0.45:
            jour = ajouter_jours(exigible, aleatoire.randint(4, 30))
        elif retard < 0.72:
            jour = ajouter_jours(exigible, aleatoire.randint(31, 89))
        else:
            coussin = max(0.0, disponible)
            continue  # échéance non honorée à ce stade

        if jour <= fin_du_monde:
            versements.append((jour, montant_du, "retard"))
            dernier_versement = jour
            coussin = max(0.0, disponible - montant_du)

    return versements, dernier_versement


def _constater_resultat(echeances, versements, fin_du_monde, aleatoire, discipline):
    """Déduit la situation finale d'un crédit à partir de sa trajectoire."""
    restant = {echeance["numero_echeance"]: echeance["montant_total_du"] for echeance in echeances}
    date_reglement = {}

    file_versements = sorted(versements)
    for jour, montant, _ in file_versements:
        reste = montant
        for numero in sorted(restant):
            if restant[numero] <= 0:
                continue
            paye = min(reste, restant[numero])
            restant[numero] -= paye
            reste -= paye
            if restant[numero] <= 0:
                date_reglement[numero] = jour
            if reste <= 0:
                break

    derniere_echeance = max(echeance["date_exigible"] for echeance in echeances)
    arret = min(ajouter_jours(derniere_echeance, SEUIL_DEFAUT_JOURS), fin_du_monde)

    jours_retard_max, impayees, date_defaut = 0, 0, None
    for echeance in echeances:
        numero = echeance["numero_echeance"]
        exigible = echeance["date_exigible"]
        if exigible > arret:
            continue
        if numero in date_reglement:
            retard = (date_reglement[numero] - exigible).days
        else:
            retard = (arret - exigible).days
            if restant[numero] > 0:
                impayees += 1
        jours_retard_max = max(jours_retard_max, retard)
        if retard >= SEUIL_DEFAUT_JOURS and restant[numero] > 0 and date_defaut is None:
            date_defaut = ajouter_jours(exigible, SEUIL_DEFAUT_JOURS)

    dernier_versement = max((jour for jour, _, _ in file_versements), default=None)
    abandon = (
        impayees >= 3
        and dernier_versement is not None
        and (arret - dernier_versement).days >= SEUIL_ABANDON_JOURS
    )
    restructure = impayees >= 2 and date_defaut is None and discipline > 0.60 and aleatoire.random() < 0.15

    capital_restant = sum(max(0, valeur) for valeur in restant.values())
    censure = derniere_echeance > fin_du_monde

    if date_defaut is not None or abandon:
        statut = "DEFAUT_EXPERIMENTAL"
    elif restructure:
        statut = "RESTRUCTURE"
    elif capital_restant > 0 and censure:
        statut = "EN_COURS"
    elif capital_restant > 0:
        statut = "DEFAUT_EXPERIMENTAL" if jours_retard_max >= SEUIL_DEFAUT_JOURS else "EN_COURS"
    elif jours_retard_max > 5:
        statut = "SOLDE_AVEC_RETARD"
    else:
        statut = "SOLDE"

    en_defaut = statut in ("DEFAUT_EXPERIMENTAL", "RESTRUCTURE")
    return {
        "date_arret_observation": arret,
        "jours_retard_max": max(0, jours_retard_max),
        "nombre_echeances_impayees": impayees,
        "capital_restant_du": capital_restant,
        "statut_final": statut,
        "defaut_experimental": 1 if en_defaut else 0,
        "date_survenue_defaut": date_defaut.isoformat() if date_defaut else "",
        "observation_censuree": 1 if censure else 0,
    }


def derouler_cycle_credit(contexte, biais_acceptation, biais_paiement):
    """Déroule le cycle complet pour tous les clients, dans l'ordre du temps.

    Les deux biais sont les molettes de calibration : ils décalent la sévérité
    d'octroi et la facilité de paiement jusqu'à ce que l'institution atteigne
    ses cibles de taux d'acceptation et de taux de défaut.
    """
    clients = contexte["clients"]
    graine = contexte["graine"]
    fin_du_monde = contexte["fin_du_monde"]
    capacites = contexte["capacites"]
    profils = {ligne["identifiant_client"]: ligne for ligne in contexte["profils_latents"]}
    profils_agents = {ligne["identifiant_agent"]: ligne for ligne in contexte["profils_agents"]}
    activites_par_client = {}
    for activite in contexte["activites"]:
        activites_par_client.setdefault(activite["identifiant_client"], []).append(activite)

    demandes, decisions, credits, echeances_lignes, paiements = [], [], [], [], []
    releves_instruction, resultats, contrefactuels = [], [], []

    # Décalages de numérotation : les identifiants restent uniques quand
    # plusieurs institutions sont générées dans la même exécution.
    decalages = contexte.get("decalages", {})
    numero_demande = decalages.get("demande", 0)
    numero_credit = decalages.get("credit", 0)
    numero_echeance = decalages.get("echeance", 0)
    numero_paiement = decalages.get("paiement", 0)

    for client in clients:
        identifiant_client = client["identifiant_client"]
        profil = profils[identifiant_client]
        discipline = float(profil["discipline_paiement"])
        appetence = float(profil["appetence_credit"])
        aleatoire = flux(graine, "cycle", identifiant_client)

        entree = date.fromisoformat(client["date_entree_relation"])
        sortie = date.fromisoformat(client["date_sortie_relation"]) if client["date_sortie_relation"] else fin_du_monde
        debut = max(entree, contexte["debut_du_monde"])
        if min(sortie, fin_du_monde) < debut:
            continue

        historique = {"credits": 0, "retards": 0, "defauts": 0}
        libre_a_partir_de = debut
        rang = 0

        for mois in suite_de_mois(debut, min(sortie, fin_du_monde)):
            jour_demande = date(int(mois[:4]), int(mois[5:]), aleatoire.randint(3, 26))
            # Une demande déposée dans les toutes dernières semaines verrait sa
            # décision et son décaissement tomber après la fin du monde : elle
            # appartient au monde suivant, pas à celui-ci.
            if jour_demande > ajouter_jours(fin_du_monde, -40):
                continue
            if jour_demande < libre_a_partir_de or jour_demande > min(sortie, fin_du_monde):
                continue

            capacite = capacites.get((identifiant_client, mois))
            if capacite is None:
                continue

            # Un client demande d'autant plus qu'il est entreprenant et que sa
            # trésorerie est tendue. Le tout premier crédit demande un peu
            # d'ancienneté de relation.
            tension = 1.0 if capacite["capacite_mensuelle"] > 0 else 1.5
            anciennete = ecart_en_mois(entree, jour_demande)
            if rang == 0 and anciennete < 2:
                continue
            probabilite = borner(0.055 * (0.4 + appetence) * tension * (1.25 if rang > 0 else 1.0), 0.0, 0.35)
            if aleatoire.random() > probabilite:
                continue

            activites_client = activites_par_client.get(identifiant_client, [])
            produit = _produit_eligible(
                contexte["produits"], contexte["mix_produits"],
                client["code_secteur_principal"], jour_demande, aleatoire,
            )
            agent = _agent_disponible(contexte["agents"], client["identifiant_agence"], jour_demande, aleatoire)
            if produit is None or agent is None:
                continue

            lignes_releve = construire_releves(
                client, activites_client, contexte["situations_par_activite"], capacites,
                contexte["dettes"], jour_demande, "instruction_demande", aleatoire,
            )
            if not lignes_releve:
                continue
            releves_instruction.extend(lignes_releve)

            recettes_declarees = sum(ligne["recettes_mensuelles_declarees"] for ligne in lignes_releve)
            charges_declarees = sum(ligne["charges_mensuelles_declarees"] for ligne in lignes_releve)
            dette_externe = lignes_releve[0]["dette_externe_mensualite"] or 0

            rang += 1
            numero_demande += 1
            identifiant_demande = f"DEM-{numero_demande:06d}"

            durees = {
                duree: poids for duree, poids in DUREES_PRIVILEGIEES.items()
                if produit["duree_min_mois"] <= duree <= produit["duree_max_mois"]
            }
            duree = tirage_pondere(aleatoire, durees or {produit["duree_min_mois"]: 1})

            # Le montant se raisonne sur la marge nette, pas sur le chiffre
            # d'affaires : un commerçant à 250 000 F de recettes et 12 % de
            # marge ne rembourse pas sur 250 000 F. Un client sur cinq demande
            # tout de même au-delà de ce qu'il peut porter — ce sont ces
            # dossiers-là que l'instruction doit savoir écarter.
            revenu_net_declare = max(5000.0, recettes_declarees - charges_declarees)
            ambition = aleatoire.uniform(0.90, 1.40) if aleatoire.random() < 0.20 else aleatoire.uniform(0.30, 0.75)
            montant = duree * revenu_net_declare * ambition
            montant *= contexte["profil_institution"]["multiplicateur_montant"]
            montant *= 1 + 0.12 * (rang - 1)
            montant = int(borner(round(montant / 5000) * 5000, produit["montant_min"], produit["montant_max"]))

            demande = {
                "identifiant_demande": identifiant_demande,
                "identifiant_client": identifiant_client,
                "identifiant_institution": client["identifiant_institution"],
                "identifiant_agent": agent["identifiant_agent"],
                "identifiant_produit": produit["identifiant_produit"],
                "date_demande": jour_demande.isoformat(),
                "montant_demande": montant,
                "duree_demandee_mois": duree,
                "objet_credit": _objet(produit["code_produit"]),
                "identifiant_releve_instruction": None,
                "rang_demande_client": rang,
            }
            demande["_releve"] = lignes_releve[0]
            demandes.append(demande)

            # ---- Décision -------------------------------------------------
            echeance_estimee = montant / duree
            revenu_declare = max(1.0, recettes_declarees - charges_declarees)
            charge_echeance = echeance_estimee / revenu_declare
            charge_externe = float(dette_externe) / revenu_declare
            charge_dette = charge_echeance + charge_externe
            severite_agent = float(profils_agents[agent["identifiant_agent"]]["severite"])

            score = (
                1.9
                - 2.3 * min(charge_dette, 2.5)
                + 0.30 * math.log1p(anciennete)
                + 0.22 * math.log1p(client["anciennete_activite_mois_a_entree"])
                + 0.35 * historique["credits"]
                - 0.55 * historique["retards"]
                - 2.20 * historique["defauts"]
                - 2.6 * (severite_agent - 0.5)
                + aleatoire.gauss(0, 0.35)
                + biais_acceptation
            )
            probabilite_acceptation = _sigmoide(score)
            tirage = aleatoire.random()

            if tirage < probabilite_acceptation:
                statut, motif = "ACCEPTEE", ""
            elif aleatoire.random() < 0.12:
                statut = "AJOURNEE" if aleatoire.random() < 0.6 else "ANNULEE_CLIENT"
                motif = "dossier_incomplet" if statut == "AJOURNEE" else ""
            else:
                statut = "REFUSEE"
                motif = _motif_refus(
                    charge_echeance, charge_externe, historique, anciennete,
                    client["anciennete_activite_mois_a_entree"], aleatoire,
                )

            jour_decision = ajouter_jours(jour_demande, aleatoire.randint(1, 21))
            montant_accorde = duree_accordee = ""
            if statut == "ACCEPTEE":
                montant_accorde = montant
                if aleatoire.random() < 0.30:
                    montant_accorde = int(round(montant * aleatoire.uniform(0.60, 0.90) / 5000) * 5000)
                    montant_accorde = max(produit["montant_min"], montant_accorde)
                duree_accordee = duree if aleatoire.random() < 0.85 else min(duree + 3, produit["duree_max_mois"])

            decisions.append({
                "identifiant_decision": f"DEC-{numero_demande:06d}",
                "identifiant_demande": identifiant_demande,
                "identifiant_institution": client["identifiant_institution"],
                "date_decision": jour_decision.isoformat(),
                "statut": statut,
                "motif_principal": motif,
                "montant_accorde": montant_accorde,
                "duree_accordee_mois": duree_accordee,
            })

            if statut != "ACCEPTEE":
                libre_a_partir_de = ajouter_mois(jour_demande, 3)
                if statut == "REFUSEE":
                    contrefactuels.append(_simuler_contrefactuel(
                        demande, montant, duree, produit, jour_decision, discipline,
                        capacites, identifiant_client, capacite, fin_du_monde,
                        flux(graine, "contrefactuel", identifiant_demande), biais_paiement,
                    ))
                continue

            # ---- Crédit, échéancier, paiements ----------------------------
            numero_credit += 1
            identifiant_credit = f"CRD-{numero_credit:06d}"
            decaissement = ajouter_jours(jour_decision, aleatoire.randint(0, 14))
            differe = 0
            if produit["type_amortissement"] == "differe_puis_mensuel":
                differe = aleatoire.randint(3, produit["differe_max_mois"])

            lignes_echeancier = _echeancier(montant_accorde, duree_accordee, decaissement, differe)
            credits.append({
                "identifiant_credit": identifiant_credit,
                "identifiant_demande": identifiant_demande,
                "identifiant_institution": client["identifiant_institution"],
                "date_decaissement": decaissement.isoformat(),
                "montant_decaisse": montant_accorde,
                "duree_mois": duree_accordee,
                "type_amortissement": produit["type_amortissement"],
                "differe_mois": differe,
                "echeance_theorique": lignes_echeancier[0]["montant_total_du"],
                "date_premiere_echeance": lignes_echeancier[0]["date_exigible"].isoformat(),
                "date_derniere_echeance_prevue": lignes_echeancier[-1]["date_exigible"].isoformat(),
            })

            identifiants_echeances = {}
            for ligne in lignes_echeancier:
                numero_echeance += 1
                identifiants_echeances[ligne["numero_echeance"]] = f"ECH-{numero_echeance:07d}"
                echeances_lignes.append({
                    "identifiant_echeance": identifiants_echeances[ligne["numero_echeance"]],
                    "identifiant_credit": identifiant_credit,
                    "identifiant_institution": client["identifiant_institution"],
                    "numero_echeance": ligne["numero_echeance"],
                    "date_exigible": ligne["date_exigible"].isoformat(),
                    "montant_capital_du": ligne["montant_capital_du"],
                    "montant_interet_du": ligne["montant_interet_du"],
                    "montant_total_du": ligne["montant_total_du"],
                })

            versements, _ = _simuler_paiements(
                lignes_echeancier, discipline, capacites, identifiant_client,
                capacite["coussin_estime"], fin_du_monde, aleatoire, biais_paiement,
            )

            file_attente = sorted(versements)
            numero_courant = 1
            for jour, montant_paye, nature in file_attente:
                numero_paiement += 1
                rattachement = ""
                if nature in ("complet", "retard", "partiel"):
                    rattachement = identifiants_echeances.get(numero_courant, "")
                if nature in ("complet", "retard", "complement"):
                    numero_courant += 1
                paiements.append({
                    "identifiant_paiement": f"PAI-{numero_paiement:07d}",
                    "identifiant_credit": identifiant_credit,
                    "identifiant_echeance": rattachement,
                    "identifiant_institution": client["identifiant_institution"],
                    "date_paiement": jour.isoformat(),
                    "montant_paye": int(montant_paye),
                    "canal_paiement": _canal(jour, aleatoire),
                })

            resultat = _constater_resultat(lignes_echeancier, versements, fin_du_monde, aleatoire, discipline)
            resultats.append({
                "identifiant_credit": identifiant_credit,
                "identifiant_institution": client["identifiant_institution"],
                "date_arret_observation": resultat["date_arret_observation"].isoformat(),
                "jours_retard_max": resultat["jours_retard_max"],
                "nombre_echeances_impayees": resultat["nombre_echeances_impayees"],
                "capital_restant_du": resultat["capital_restant_du"],
                "statut_final": resultat["statut_final"],
                "defaut_experimental": resultat["defaut_experimental"],
                "date_survenue_defaut": resultat["date_survenue_defaut"],
                "observation_censuree": resultat["observation_censuree"],
            })

            historique["credits"] += 1
            if resultat["jours_retard_max"] > 30:
                historique["retards"] += 1
            if resultat["defaut_experimental"] == 1:
                historique["defauts"] += 1

            fin_credit = lignes_echeancier[-1]["date_exigible"]
            libre_a_partir_de = ajouter_mois(fin_credit, -1 if resultat["defaut_experimental"] == 0 else 6)

    return {
        "demandes": demandes,
        "decisions": decisions,
        "credits": credits,
        "echeances": echeances_lignes,
        "paiements": paiements,
        "releves_instruction": releves_instruction,
        "resultats": resultats,
        "contrefactuels": contrefactuels,
    }


def _simuler_contrefactuel(demande, montant, duree, produit, jour_decision, discipline,
                           capacites, identifiant_client, capacite, fin_du_monde,
                           aleatoire, biais_paiement):
    """Ce qui serait arrivé si la demande refusée avait été acceptée.

    Aucune institution réelle ne peut observer cela. Le simulateur, lui, déroule
    la branche parallèle et range le résultat hors des données observables :
    c'est ce qui permettra d'évaluer honnêtement une méthode de reject inference.
    """
    decaissement = ajouter_jours(jour_decision, aleatoire.randint(0, 14))
    differe = aleatoire.randint(3, produit["differe_max_mois"]) if produit["type_amortissement"] == "differe_puis_mensuel" else 0
    echeancier = _echeancier(montant, duree, decaissement, differe)
    versements, _ = _simuler_paiements(
        echeancier, discipline, capacites, identifiant_client,
        capacite["coussin_estime"], fin_du_monde, aleatoire, biais_paiement,
    )
    resultat = _constater_resultat(echeancier, versements, fin_du_monde, aleatoire, discipline)
    return {
        "identifiant_demande": demande["identifiant_demande"],
        "identifiant_institution": demande["identifiant_institution"],
        "aurait_ete_decaisse": 1 if aleatoire.random() < 0.92 else 0,
        "defaut_contrefactuel": resultat["defaut_experimental"],
        "jours_retard_max_contrefactuel": resultat["jours_retard_max"],
        "capital_perdu_contrefactuel": resultat["capital_restant_du"] if resultat["defaut_experimental"] else 0,
    }


def _objet(code_produit):
    return {
        "MICROCREDIT_GENERAL": "tresorerie",
        "FONDS_ROULEMENT": "achat_stock",
        "CREDIT_COMMERCE": "achat_stock",
        "CREDIT_AGRICOLE": "intrants",
        "CREDIT_EQUIPEMENT": "equipement",
    }[code_produit]


def _motif_refus(charge_echeance, charge_externe, historique, anciennete, anciennete_activite, aleatoire):
    """Désigne la contrainte qui a réellement bloqué le dossier.

    Le motif n'est pas une cascade de seuils mais le terme le plus pénalisant du
    score : c'est ce qui en fait une vérité terrain utilisable pour évaluer les
    explications que produira un modèle.
    """
    contributions = {
        "capacite_insuffisante": 2.3 * min(charge_echeance, 2.5),
        "endettement_eleve": 2.3 * min(charge_externe, 2.5),
        "historique_incidents": 0.55 * historique["retards"] + 2.20 * historique["defauts"],
        "activite_trop_recente": max(
            0.0, 1.6 - 0.30 * math.log1p(anciennete) - 0.22 * math.log1p(anciennete_activite)
        ),
    }
    motif, poids = max(contributions.items(), key=lambda couple: couple[1])
    if poids < 0.8:
        # Aucune contrainte ne domine : le dossier tombe sur la sévérité de
        # l'agent, qui la formule comme un défaut de garantie ou de pièces.
        return "garantie_insuffisante" if aleatoire.random() < 0.5 else "dossier_incomplet"
    return motif


def _canal(jour, aleatoire):
    """Le mobile money gagne du terrain sur la période : c'est une dérive douce."""
    part_mobile = 0.18 + 0.05 * (jour.year - 2021)
    tirage = aleatoire.random()
    if tirage < part_mobile:
        return "mobile_money"
    if tirage < part_mobile + 0.15:
        return "collecteur"
    return "agence"
