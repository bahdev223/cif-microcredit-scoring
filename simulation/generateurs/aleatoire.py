"""Flux aléatoires reproductibles.

Chaque entité du monde tire ses valeurs dans son propre flux, dérivé de la
graine globale et de son identifiant. Deux conséquences utiles :

- l'ordre d'exécution n'a aucune importance, donc on pourra paralléliser la
  génération sans changer un seul chiffre ;
- ajouter un client ne décale pas les tirages de tous les autres, donc un monde
  reste comparable à lui-même d'une version à l'autre.
"""

import hashlib
import math
import random


def flux(graine, *cles):
    """Retourne un générateur aléatoire propre au couple (graine, clés)."""
    empreinte = hashlib.sha256("|".join(str(cle) for cle in cles).encode("utf-8")).hexdigest()
    return random.Random(graine ^ int(empreinte[:16], 16))


def tirage_pondere(aleatoire, poids):
    """Tire une clé selon un dictionnaire {clé: poids}, poids nuls ignorés."""
    candidats = [(cle, valeur) for cle, valeur in sorted(poids.items()) if valeur > 0]
    total = sum(valeur for _, valeur in candidats)
    seuil = aleatoire.random() * total
    cumul = 0.0
    for cle, valeur in candidats:
        cumul += valeur
        if seuil <= cumul:
            return cle
    return candidats[-1][0]


def log_normale(aleatoire, mediane, sigma_log):
    """Tire une valeur positive de médiane donnée."""
    return mediane * math.exp(aleatoire.gauss(0.0, sigma_log))


def borner(valeur, minimum, maximum):
    return max(minimum, min(maximum, valeur))


def beta_bornee(aleatoire, alpha, beta, decalage=0.0, minimum=0.01, maximum=0.99):
    """Tire une valeur dans ]0, 1[ puis la décale sans sortir des bornes."""
    return borner(aleatoire.betavariate(alpha, beta) + decalage, minimum, maximum)
