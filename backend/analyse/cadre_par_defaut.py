"""Cadre d'analyse appliqué tant que l'institution n'a pas défini le sien.

Ce n'est pas une formule codée en dur : c'est une **configuration** exprimée
dans le même langage que celle d'une institution, et exécutée par le même
moteur. Le jour où l'institution crée son cadre et l'associe à un produit,
c'est le sien qui s'applique, sans qu'une ligne de code métier ne change.

Il est délibérément minimal et discutable — la cascade la plus répandue, rien
de plus. Sa vocation est d'être remplacé lors de la première visite.
"""

CODE = "DEFAUT"
NOM = "Cadre par défaut"

DEFINITION = [
    {"code": "RECETTES_ACT", "nom": "Recettes de l'activité", "mode": "SAISIE", "sens": "CREDIT",
     "type": "MONTANT", "obligatoire": True, "section_code": "ACTIVITE", "section_nom": "Activité"},
    {"code": "CHARGES_ACT", "nom": "Charges de l'activité", "mode": "SAISIE", "sens": "DEBIT",
     "type": "MONTANT", "obligatoire": False, "section_code": "ACTIVITE", "section_nom": "Activité"},
    {"code": "RESULTAT_ACT", "nom": "Résultat de l'activité", "mode": "CALCUL", "sens": "RESULTAT",
     "type": "MONTANT", "formule": "RECETTES_ACT - CHARGES_ACT", "role": "RESULTAT_ACTIVITE",
     "section_code": "ACTIVITE", "section_nom": "Activité"},
    {"code": "AUTRES_REVENUS", "nom": "Autres revenus du ménage", "mode": "SAISIE", "sens": "CREDIT",
     "type": "MONTANT", "obligatoire": False, "section_code": "MENAGE", "section_nom": "Ménage"},
    {"code": "CHARGES_MENAGE", "nom": "Charges du ménage", "mode": "SAISIE", "sens": "DEBIT",
     "type": "MONTANT", "obligatoire": False, "section_code": "MENAGE", "section_nom": "Ménage"},
    {"code": "ENGAGEMENTS", "nom": "Engagements existants", "mode": "SAISIE", "sens": "DEBIT",
     "type": "MONTANT", "obligatoire": False, "section_code": "ENGAGEMENTS", "section_nom": "Engagements"},
    {"code": "MARGE_DISPONIBLE", "nom": "Marge disponible", "mode": "CALCUL", "sens": "RESULTAT",
     "type": "MONTANT", "formule": "RESULTAT_ACT + AUTRES_REVENUS - CHARGES_MENAGE - ENGAGEMENTS", "role": "MARGE_DISPONIBLE",
     "section_code": "CAPACITE", "section_nom": "Capacité"},
    {"code": "PRESSION", "nom": "Pression de remboursement", "mode": "CALCUL", "sens": "RESULTAT",
     "type": "POURCENTAGE", "formule": "ECHEANCE_PROJETEE / MARGE_DISPONIBLE * 100", "role": "PRESSION_REMBOURSEMENT",
     "section_code": "CAPACITE", "section_nom": "Capacité"},
]

# Les seuils appartiennent à l'institution. Ceux-ci sont des repères de lecture
# proposés par défaut, à corriger dès le premier échange métier.
REGLES = [
    {"code": "R_ECHEANCE_SUP_MARGE", "nom": "Échéance supérieure à la marge",
     "condition": "PRESSION > 100", "resultat": "POINT_ATTENTION",
     "message": "L'échéance projetée dépasse la marge disponible."},
    {"code": "R_PRESSION_ELEVEE", "nom": "Pression élevée",
     "condition": "PRESSION > 80 ET PRESSION <= 100", "resultat": "POINT_ATTENTION",
     "message": "L'échéance absorbe plus de 80 % de la marge disponible."},
    {"code": "R_MARGE_NULLE", "nom": "Marge absente",
     "condition": "MARGE_DISPONIBLE <= 0", "resultat": "POINT_ATTENTION",
     "message": "Les charges déclarées absorbent la totalité des recettes."},
    {"code": "R_PRESSION_SOUTENABLE", "nom": "Pression soutenable",
     "condition": "PRESSION > 0 ET PRESSION < 50", "resultat": "POINT_FAVORABLE",
     "message": "L'échéance reste inférieure à la moitié de la marge disponible."},
]

# Correspondance entre les champs relevés sur la demande et les rubriques du
# cadre par défaut. Un cadre configuré par l'institution portera ses propres
# codes ; les valeurs viendront alors du formulaire qu'elle aura défini.
CHAMPS_DEMANDE = {
    "RECETTES_ACT": "recettes_activite",
    "CHARGES_ACT": "charges_activite",
    "AUTRES_REVENUS": "autres_revenus_menage",
    "CHARGES_MENAGE": "charges_menage",
    "ENGAGEMENTS": "mensualite_dette_existante",
}


def valeurs_depuis_demande(demande):
    """Valeurs de saisie, lues sur la demande ou sur ce qu'elle a enregistré.

    Les valeurs saisies dans un formulaire dynamique sont conservées telles
    quelles ; à défaut, on retombe sur les champs fixes de la demande.
    """
    if demande.valeurs_cadre:
        return dict(demande.valeurs_cadre)
    return {code: getattr(demande, champ, 0) or 0 for code, champ in CHAMPS_DEMANDE.items()}
