"""Manipulations de dates et de mois.

Le monde a deux horloges : une horloge mensuelle pour l'économie et une horloge
journalière pour les mouvements d'argent. Ces fonctions font le lien entre les
deux, sans dépendance extérieure.
"""

from calendar import monthrange
from datetime import date, timedelta


def cle_mois(jour):
    """Retourne le mois d'une date sous la forme AAAA-MM."""
    return f"{jour.year:04d}-{jour.month:02d}"


def mois_vers_couple(mois):
    annee, numero = mois.split("-")
    return int(annee), int(numero)


def ajouter_mois(jour, nombre):
    """Décale une date d'un nombre de mois en ramenant au dernier jour utile.

    Le 31 janvier plus un mois donne le 28 ou le 29 février : c'est la règle
    d'échéancier la plus courante et la plus simple à expliquer.
    """
    total = jour.month - 1 + nombre
    annee = jour.year + total // 12
    numero = total % 12 + 1
    dernier_jour = monthrange(annee, numero)[1]
    return date(annee, numero, min(jour.day, dernier_jour))


def suite_de_mois(depart, fin):
    """Liste les mois AAAA-MM entre deux dates, bornes comprises."""
    mois, resultat = date(depart.year, depart.month, 1), []
    limite = date(fin.year, fin.month, 1)
    while mois <= limite:
        resultat.append(cle_mois(mois))
        mois = ajouter_mois(mois, 1)
    return resultat


def premier_jour_du_mois(mois):
    annee, numero = mois_vers_couple(mois)
    return date(annee, numero, 1)


def jour_dans_le_mois(aleatoire, mois):
    annee, numero = mois_vers_couple(mois)
    return date(annee, numero, aleatoire.randint(1, monthrange(annee, numero)[1]))


def ecart_en_mois(depart, fin):
    return (fin.year - depart.year) * 12 + (fin.month - depart.month)


def ajouter_jours(jour, nombre):
    return jour + timedelta(days=nombre)
