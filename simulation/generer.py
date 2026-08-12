"""Générateur du monde synthétique des institutions fictives.

Le monde se construit par couches numérotées, du plus stable au plus vivant.
Chaque couche ne dépend que des précédentes : c'est ce qui garantit qu'un
client ne naît jamais avant l'agence à laquelle il est rattaché, et qu'un
paiement n'existe jamais avant le crédit qu'il rembourse.

    01 institutions          06 clients            11 crédits
    02 agences               07 activités          12 échéances
    03 agents de crédit      07b relevés           13 paiements
    04 produits de crédit    08 situations         14 résultats observés
    05 secteurs d'activité   09 demandes           puis dégradation volontaire
                             10 décisions

Deux familles de sorties :

    donnees/synthetiques/brutes/   ce que l'institution aurait enregistré,
                                   seule source autorisée pour l'entraînement
    donnees/synthetiques/verite/   les paramètres cachés du simulateur,
                                   interdits à tout laboratoire d'entraînement

Exécution explicite uniquement :

    python simulation/generer.py
    python simulation/generer.py --institution INS-001 --clients 100

Même configuration et même graine produisent exactement les mêmes fichiers.
Le contrat de chaque table est décrit dans
documentation/07-dictionnaire-donnees-synthetiques.md.
"""

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

from generateurs import economie, population, qualite, referentiels
from generateurs.credit import derouler_cycle_credit
from generateurs.institutions import generer_institutions

RACINE = Path(__file__).resolve().parents[1]
CONFIGURATION = RACINE / "simulation" / "configuration"
BRUTES = RACINE / "donnees" / "synthetiques" / "brutes"
TRAITEES = RACINE / "donnees" / "synthetiques" / "traitees"
VERITE = RACINE / "donnees" / "synthetiques" / "verite"

TOLERANCE_ACCEPTATION = 0.02
TOLERANCE_DEFAUT = 0.02
ITERATIONS_CALIBRATION = 8


def lire_yaml(nom):
    return yaml.safe_load((CONFIGURATION / nom).read_text(encoding="utf-8"))


def ecrire_csv(dossier, nom, lignes):
    """Écrit une table triée par clé primaire et retourne son chemin."""
    if not lignes:
        raise ValueError(f"Aucune ligne produite pour {nom}")
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / nom
    colonnes = list(lignes[0])
    ordonnees = sorted(lignes, key=lambda ligne: [str(ligne[colonne]) for colonne in colonnes[:2]])
    with chemin.open("w", newline="\n", encoding="utf-8") as fichier:
        ecrivain = csv.DictWriter(fichier, fieldnames=colonnes, lineterminator="\n")
        ecrivain.writeheader()
        ecrivain.writerows(ordonnees)
    return chemin


def empreinte(chemin):
    return hashlib.sha256(chemin.read_bytes()).hexdigest()


def commit_du_code():
    try:
        resultat = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=RACINE, capture_output=True, text=True, check=True
        )
        return resultat.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def _logit(valeur):
    valeur = min(max(valeur, 0.01), 0.99)
    return __import__("math").log(valeur / (1 - valeur))


def calibrer_cycle(contexte, profil_latent, journal):
    """Ajuste la sévérité d'octroi et la facilité de paiement sur les cibles.

    Les cibles de l'institution sont des paramètres du monde, pas des résultats
    à espérer : on déroule le cycle plusieurs fois en décalant deux molettes,
    jusqu'à retomber sur le taux d'acceptation et le taux de défaut visés. La
    boucle est déterministe, donc la reproductibilité est préservée.
    """
    cible_acceptation = profil_latent["taux_acceptation_cible"]
    cible_defaut = profil_latent["taux_defaut_experimental_cible"]
    biais_acceptation, biais_paiement = 0.0, 0.0
    meilleur, ecart_minimal = None, None

    for iteration in range(1, ITERATIONS_CALIBRATION + 1):
        tables = derouler_cycle_credit(contexte, biais_acceptation, biais_paiement)
        decisions = tables["decisions"]
        acceptees = sum(1 for ligne in decisions if ligne["statut"] == "ACCEPTEE")
        observables = [ligne for ligne in tables["resultats"] if ligne["observation_censuree"] == 0]
        defauts = sum(1 for ligne in observables if ligne["defaut_experimental"] == 1)

        taux_acceptation = acceptees / len(decisions) if decisions else 0.0
        taux_defaut = defauts / len(observables) if observables else 0.0
        ecart = abs(taux_acceptation - cible_acceptation) + abs(taux_defaut - cible_defaut)

        if ecart_minimal is None or ecart < ecart_minimal:
            meilleur, ecart_minimal = tables, ecart
            mesures = {"taux_acceptation": taux_acceptation, "taux_defaut": taux_defaut,
                       "biais_acceptation": biais_acceptation, "biais_paiement": biais_paiement,
                       "iterations": iteration}

        # Sur un petit échantillon, un seul crédit peut peser deux points de
        # taux de défaut : viser mieux que la granularité des données n'a pas de
        # sens et ferait tourner la calibration pour rien.
        tolerance_acceptation = max(TOLERANCE_ACCEPTATION, 1.5 / max(1, len(decisions)))
        tolerance_defaut = max(TOLERANCE_DEFAUT, 1.5 / max(1, len(observables)))
        if (abs(taux_acceptation - cible_acceptation) <= tolerance_acceptation
                and abs(taux_defaut - cible_defaut) <= tolerance_defaut):
            break

        biais_acceptation += 0.8 * (_logit(cible_acceptation) - _logit(taux_acceptation))
        biais_paiement += 3.0 * (taux_defaut - cible_defaut)

    journal.append(mesures)
    return meilleur


def generer_institution(institution, profil_latent, mix_sectoriel, mix_produits, configurations,
                        graine, debut_du_monde, fin_du_monde, nombre_clients, decalages, journal):
    """Déroule les quatorze couches pour une institution."""
    nombre_agences, nombre_agents = referentiels.dimensionner(profil_latent, nombre_clients)

    agences = referentiels.generer_agences(
        institution, profil_latent, nombre_agences, graine, debut_du_monde, fin_du_monde,
        decalages["agence"] + 1,
    )
    agents, profils_agents = referentiels.generer_agents_credit(
        institution, profil_latent, agences, nombre_agents, graine, debut_du_monde, fin_du_monde,
        decalages["agent"] + 1,
    )
    clients, profils_latents = population.generer_clients(
        institution, profil_latent, mix_sectoriel, agences, nombre_clients,
        graine, debut_du_monde, fin_du_monde, decalages["client"] + 1,
    )
    activites, parametres_activites = population.generer_activites(
        clients, profils_latents, configurations["parametres_secteurs"], mix_sectoriel,
        profil_latent, graine, fin_du_monde, decalages["activite"] + 1,
    )

    evenements, effets = economie.generer_evenements(
        clients, profils_latents, configurations["contexte_macro"], graine, debut_du_monde, fin_du_monde
    )
    situations, situations_par_activite = economie.generer_situations_mensuelles(
        clients, activites, parametres_activites, configurations["contexte_macro"], effets,
        profil_latent, graine, debut_du_monde, fin_du_monde,
    )
    capacites_lignes, capacites = economie.generer_capacite_mensuelle(
        clients, situations, graine, debut_du_monde, fin_du_monde
    )
    dettes = economie.preparer_dettes_externes(clients, profils_latents, graine)
    releves_base = economie.generer_releves_de_base(
        clients, activites, situations_par_activite, capacites, dettes, graine, debut_du_monde, fin_du_monde
    )

    contexte = {
        "clients": clients,
        "activites": activites,
        "profils_latents": profils_latents,
        "profils_agents": profils_agents,
        "agents": agents,
        "produits": configurations["produits"],
        "mix_produits": mix_produits,
        "situations_par_activite": situations_par_activite,
        "capacites": capacites,
        "dettes": dettes,
        "profil_institution": profil_latent,
        "graine": graine,
        "debut_du_monde": debut_du_monde,
        "fin_du_monde": fin_du_monde,
        "decalages": {
            "demande": decalages["demande"],
            "credit": decalages["credit"],
            "echeance": decalages["echeance"],
            "paiement": decalages["paiement"],
        },
    }
    cycle = calibrer_cycle(contexte, profil_latent, journal)

    # Les relevés d'instruction naissent avec les demandes : on les fusionne
    # avec les relevés de base, on numérote l'ensemble dans l'ordre du temps,
    # puis on rattache chaque demande au relevé qui l'a instruite.
    releves = releves_base + cycle["releves_instruction"]
    releves.sort(key=lambda ligne: (ligne["identifiant_client"], ligne["date_releve"], ligne["identifiant_activite"]))
    for rang, releve in enumerate(releves, decalages["releve"] + 1):
        releve["identifiant_releve"] = f"REL-{rang:06d}"
    for demande in cycle["demandes"]:
        demande["identifiant_releve_instruction"] = demande.pop("_releve")["identifiant_releve"]

    releves, journal_qualite = qualite.degrader_releves(
        releves, profil_latent["facteur_qualite_donnees"], graine, decalages["injection"] + 1
    )

    return {
        "agences": agences,
        "agents": agents,
        "profils_agents": profils_agents,
        "clients": clients,
        "profils_latents": profils_latents,
        "activites": activites,
        "parametres_activites": parametres_activites,
        "releves": releves,
        "evenements": evenements,
        "situations": situations,
        "capacites": capacites_lignes,
        "demandes": cycle["demandes"],
        "decisions": cycle["decisions"],
        "credits": cycle["credits"],
        "echeances": cycle["echeances"],
        "paiements": cycle["paiements"],
        "resultats": cycle["resultats"],
        "contrefactuels": cycle["contrefactuels"],
        "qualite": journal_qualite,
    }


def ecrire_manifeste(chemins, graine, version, journal_calibration, arguments):
    manifeste = {
        "version_monde": version,
        "graine_aleatoire": graine,
        "scenario": arguments.scenario,
        "institutions": arguments.institution or "toutes",
        "clients_par_institution": arguments.clients or "cible du profil",
        "date_generation": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit_code": commit_du_code(),
        "calibration": journal_calibration,
        "fichiers": {
            str(chemin.relative_to(RACINE)).replace("\\", "/"): {
                "lignes": sum(1 for _ in chemin.open(encoding="utf-8")) - 1,
                "sha256": empreinte(chemin),
            }
            for chemin in sorted(chemins)
        },
    }
    VERITE.mkdir(parents=True, exist_ok=True)
    chemin = VERITE / "manifeste_generation.json"
    chemin.write_text(json.dumps(manifeste, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifeste


def main():
    analyseur = argparse.ArgumentParser(description="Génère le monde synthétique des institutions fictives.")
    analyseur.add_argument("--graine", type=int, default=None, help="remplace la graine de la configuration")
    analyseur.add_argument("--institution", default=None, help="identifiants séparés par une virgule, par exemple INS-001")
    analyseur.add_argument("--clients", type=int, default=None, help="nombre de clients par institution")
    analyseur.add_argument("--scenario", default=None, help="scénario macroéconomique, par défaut celui de la configuration")
    arguments = analyseur.parse_args()

    parametres = lire_yaml("simulation.yaml")
    configuration_institutions = lire_yaml("institutions.yaml")
    configuration_produits = lire_yaml("produits_credit.yaml")
    configuration_secteurs = lire_yaml("secteurs_activite.yaml")
    configuration_macro = lire_yaml("contexte_macro.yaml")

    graine = arguments.graine if arguments.graine is not None else parametres["graine_aleatoire"]
    arguments.scenario = arguments.scenario or parametres.get("scenario", "base")
    debut_du_monde = date.fromisoformat(parametres["date_debut"])
    fin_du_monde = date.fromisoformat(parametres["date_fin"])

    tables_institutions = generer_institutions(configuration_institutions)
    produits = referentiels.generer_produits(configuration_produits)
    secteurs, parametres_secteurs = referentiels.generer_secteurs(configuration_secteurs)
    codes_secteurs = [ligne["code_secteur"] for ligne in secteurs]
    contexte_macro, lignes_macro = economie.construire_contexte_macro(
        configuration_macro, arguments.scenario, debut_du_monde, fin_du_monde, codes_secteurs
    )

    profils = {ligne["identifiant_institution"]: ligne for ligne in tables_institutions["latents"]}
    mix_sectoriel = {}
    for ligne in tables_institutions["mix_sectoriel"]:
        mix_sectoriel.setdefault(ligne["identifiant_institution"], {})[ligne["code_secteur"]] = float(ligne["poids_population"])
    mix_produits = {}
    for ligne in tables_institutions["mix_produits"]:
        mix_produits.setdefault(ligne["identifiant_institution"], {})[ligne["code_produit"]] = float(ligne["poids_octroi"])

    retenues = arguments.institution.split(",") if arguments.institution else None
    institutions = [
        ligne for ligne in tables_institutions["observables"]
        if retenues is None or ligne["identifiant_institution"] in retenues
    ]
    if not institutions:
        raise SystemExit(f"Aucune institution ne correspond à {arguments.institution}")

    configurations = {
        "produits": produits,
        "parametres_secteurs": parametres_secteurs,
        "contexte_macro": contexte_macro,
    }
    decalages = dict.fromkeys(
        ("agence", "agent", "client", "activite", "releve", "demande", "credit", "echeance", "paiement", "injection"), 0
    )
    cumul, journal_calibration = {}, []

    for institution in institutions:
        identifiant = institution["identifiant_institution"]
        profil_latent = {
            cle: (int(valeur) if cle in ("nombre_clients_cible", "nombre_agences", "clients_par_agent_cible")
                  else float(valeur) if cle != "identifiant_institution" else valeur)
            for cle, valeur in profils[identifiant].items()
        }
        nombre_clients = arguments.clients or profil_latent["nombre_clients_cible"]

        tables = generer_institution(
            institution, profil_latent, mix_sectoriel[identifiant], mix_produits[identifiant],
            configurations, graine, debut_du_monde, fin_du_monde, nombre_clients, decalages,
            journal_calibration,
        )
        for nom, lignes in tables.items():
            cumul.setdefault(nom, []).extend(lignes)

        decalages["agence"] += len(tables["agences"])
        decalages["agent"] += len(tables["agents"])
        decalages["client"] += len(tables["clients"])
        decalages["activite"] += len(tables["activites"])
        decalages["releve"] += len(tables["releves"])
        decalages["demande"] += len(tables["demandes"])
        decalages["credit"] += len(tables["credits"])
        decalages["echeance"] += len(tables["echeances"])
        decalages["paiement"] += len(tables["paiements"])
        decalages["injection"] += len(tables["qualite"])

    chemins = [
        ecrire_csv(BRUTES, "01_institutions.csv", tables_institutions["observables"]),
        ecrire_csv(BRUTES, "02_agences.csv", cumul["agences"]),
        ecrire_csv(BRUTES, "03_agents_credit.csv", cumul["agents"]),
        ecrire_csv(BRUTES, "04_produits_credit.csv", produits),
        ecrire_csv(BRUTES, "05_secteurs_activite.csv", secteurs),
        ecrire_csv(BRUTES, "06_clients.csv", cumul["clients"]),
        ecrire_csv(BRUTES, "07_activites.csv", cumul["activites"]),
        ecrire_csv(BRUTES, "07b_releves_activite.csv", cumul["releves"]),
        ecrire_csv(BRUTES, "09_demandes_credit.csv", cumul["demandes"]),
        ecrire_csv(BRUTES, "10_decisions_credit.csv", cumul["decisions"]),
        ecrire_csv(BRUTES, "11_credits.csv", cumul["credits"]),
        ecrire_csv(BRUTES, "12_echeances.csv", cumul["echeances"]),
        ecrire_csv(BRUTES, "13_paiements.csv", cumul["paiements"]),
        ecrire_csv(TRAITEES, "14_resultats_credit.csv", cumul["resultats"]),
        ecrire_csv(VERITE, "01_profils_institutions.csv", tables_institutions["latents"]),
        ecrire_csv(VERITE, "01_mix_sectoriel.csv", tables_institutions["mix_sectoriel"]),
        ecrire_csv(VERITE, "01_mix_produits.csv", tables_institutions["mix_produits"]),
        ecrire_csv(VERITE, "03_profils_agents.csv", cumul["profils_agents"]),
        ecrire_csv(VERITE, "05_parametres_secteurs.csv", parametres_secteurs),
        ecrire_csv(VERITE, "06_profils_latents.csv", cumul["profils_latents"]),
        ecrire_csv(VERITE, "07_parametres_activites.csv", cumul["parametres_activites"]),
        ecrire_csv(VERITE, "08_situations_mensuelles.csv", cumul["situations"]),
        ecrire_csv(VERITE, "08b_capacite_mensuelle.csv", cumul["capacites"]),
        ecrire_csv(VERITE, "09_evenements.csv", cumul["evenements"]),
        ecrire_csv(VERITE, "09b_contexte_macro.csv", lignes_macro),
        ecrire_csv(VERITE, "10_decisions_contrefactuelles.csv", cumul["contrefactuels"]),
        ecrire_csv(VERITE, "qualite_injectee.csv", cumul["qualite"]),
    ]

    manifeste = ecrire_manifeste(
        chemins, graine, configuration_institutions["version_referentiel"], journal_calibration, arguments
    )

    print(f"Monde généré avec la graine {graine}, scénario « {arguments.scenario} ».")
    for nom, details in manifeste["fichiers"].items():
        print(f"  {details['lignes']:>8} lignes  {nom}")
    for mesure in journal_calibration:
        print(
            f"Calibration en {mesure['iterations']} itérations : "
            f"acceptation {mesure['taux_acceptation']:.1%}, défaut {mesure['taux_defaut']:.1%}."
        )


if __name__ == "__main__":
    main()
