"""Référentiel cible de l'acquisition.

Une institution n'exporte pas ses données avec nos noms de colonnes. Elle
écrira `CA_MENSUEL`, `MONTANT_OCTROYE` ou `DT_ECHEANCE` là où nous attendons
`recettes`, `montant_decaisse` ou `date_exigible`.

Ce module décrit ce que la plateforme attend, et les écritures rencontrées qui
désignent la même chose. Il ne décrit pas ce que l'institution possède : c'est
la correspondance, établie fichier par fichier et validée par un humain, qui
fait le lien. Les synonymes ne servent qu'à proposer ; ils ne décident jamais.

Aucun champ n'est ici parce qu'il serait « pratique à avoir ». Chacun sert la
chaîne : identifier, rattacher, dater, ou porter un montant dont l'analyse a
besoin.
"""

TABLES = {
    "clients": {
        "libelle": "Clients",
        "role": "Les personnes suivies par l'institution.",
        "champs": {
            "identifiant_client": {
                "libelle": "Identifiant du client", "type": "TEXTE", "obligatoire": True,
                "synonymes": ("client", "client_id", "id_client", "code_client", "numero_client",
                              "matricule", "matricule_client", "reference_client", "cle_client"),
            },
            "nom_client": {
                "libelle": "Nom du client", "type": "TEXTE", "obligatoire": False,
                "synonymes": ("nom", "nom_complet", "nom_prenom", "raison_sociale", "beneficiaire",
                              "nom_beneficiaire", "intitule"),
            },
            "code_secteur_principal": {
                "libelle": "Secteur d'activité", "type": "TEXTE", "obligatoire": False,
                "synonymes": ("secteur", "secteur_activite", "activite", "branche", "filiere",
                              "domaine", "type_activite"),
            },
            "anciennete_activite_mois_a_entree": {
                "libelle": "Ancienneté de l'activité (mois)", "type": "NOMBRE", "obligatoire": False,
                "synonymes": ("anciennete", "anciennete_activite", "anciennete_mois", "duree_activite",
                              "experience", "anciennete_activite_mois"),
            },
            "date_entree_relation": {
                "libelle": "Entrée en relation", "type": "DATE", "obligatoire": False,
                "synonymes": ("date_entree", "date_adhesion", "adhesion", "date_ouverture",
                              "date_creation", "client_depuis", "date_affiliation"),
            },
            "identifiant_institution": {
                "libelle": "Institution", "type": "TEXTE", "obligatoire": False,
                "synonymes": ("institution", "sfd", "imf", "agence", "code_agence", "code_institution"),
            },
        },
    },
    "activites": {
        "libelle": "Activités économiques",
        "role": "Ce que fait le client, et depuis quand.",
        "champs": {
            "identifiant_activite": {
                "libelle": "Identifiant de l'activité", "type": "TEXTE", "obligatoire": True,
                "synonymes": ("activite_id", "id_activite", "code_activite", "reference_activite"),
            },
            "identifiant_client": {
                "libelle": "Identifiant du client", "type": "TEXTE", "obligatoire": True,
                "synonymes": ("client", "client_id", "id_client", "code_client", "matricule"),
            },
            "libelle_activite": {
                "libelle": "Libellé de l'activité", "type": "TEXTE", "obligatoire": False,
                "synonymes": ("libelle", "activite", "designation", "intitule", "nom_activite"),
            },
            "code_secteur": {
                "libelle": "Secteur", "type": "TEXTE", "obligatoire": False,
                "synonymes": ("secteur", "secteur_activite", "branche", "filiere"),
            },
            "date_debut": {
                "libelle": "Début de l'activité", "type": "DATE", "obligatoire": False,
                "synonymes": ("debut", "date_creation", "date_demarrage", "depuis"),
            },
        },
    },
    "demandes_credit": {
        "libelle": "Demandes de crédit",
        "role": "Ce qui a été demandé, et quand.",
        "champs": {
            "identifiant_demande": {
                "libelle": "Identifiant de la demande", "type": "TEXTE", "obligatoire": True,
                "synonymes": ("demande", "demande_id", "id_demande", "code_demande", "reference_demande",
                              "num_demande", "numero_demande", "dossier", "numero_dossier"),
            },
            "identifiant_client": {
                "libelle": "Identifiant du client", "type": "TEXTE", "obligatoire": True,
                "synonymes": ("client", "client_id", "id_client", "code_client", "matricule"),
            },
            "montant_demande": {
                "libelle": "Montant demandé", "type": "MONTANT", "obligatoire": True,
                "synonymes": ("montant", "montant_sollicite", "montant_demandee", "mt_demande",
                              "montant_souhaite", "somme_demandee"),
            },
            "duree_demandee_mois": {
                "libelle": "Durée demandée (mois)", "type": "NOMBRE", "obligatoire": False,
                "synonymes": ("duree", "duree_mois", "nb_mois", "duree_souhaitee", "echeancier_mois"),
            },
            "date_demande": {
                "libelle": "Date de la demande", "type": "DATE", "obligatoire": False,
                "synonymes": ("date", "date_depot", "date_dossier", "date_reception", "dt_demande"),
            },
            "objet_credit": {
                "libelle": "Objet du financement", "type": "TEXTE", "obligatoire": False,
                "synonymes": ("objet", "motif", "finalite", "destination", "objet_financement", "but"),
            },
        },
    },
    "credits": {
        "libelle": "Crédits",
        "role": "Ce qui a été effectivement accordé et décaissé.",
        "champs": {
            "identifiant_credit": {
                "libelle": "Identifiant du crédit", "type": "TEXTE", "obligatoire": True,
                "synonymes": ("credit", "credit_id", "id_credit", "code_credit", "reference_credit",
                              "num_credit", "numero_credit", "pret", "id_pret", "loan_id"),
            },
            "identifiant_demande": {
                "libelle": "Identifiant de la demande", "type": "TEXTE", "obligatoire": True,
                "synonymes": ("demande", "demande_id", "id_demande", "dossier", "numero_dossier"),
            },
            "identifiant_client": {
                "libelle": "Identifiant du client", "type": "TEXTE", "obligatoire": False,
                "synonymes": ("client", "client_id", "id_client", "code_client", "matricule"),
            },
            "montant_decaisse": {
                "libelle": "Montant décaissé", "type": "MONTANT", "obligatoire": False,
                "synonymes": ("montant", "montant_octroye", "montant_accorde", "capital", "principal",
                              "mt_credit", "montant_credit", "montant_debloque"),
            },
            "duree_mois": {
                "libelle": "Durée (mois)", "type": "NOMBRE", "obligatoire": False,
                "synonymes": ("duree", "nb_mois", "duree_credit", "nb_echeances", "nombre_echeances"),
            },
            "date_decaissement": {
                "libelle": "Date de décaissement", "type": "DATE", "obligatoire": False,
                "synonymes": ("date", "date_octroi", "date_deblocage", "date_mise_en_place",
                              "dt_decaissement", "date_credit"),
            },
        },
    },
    "echeances": {
        "libelle": "Échéances",
        "role": "Ce qui devait être payé, et à quelle date.",
        "champs": {
            "identifiant_echeance": {
                "libelle": "Identifiant de l'échéance", "type": "TEXTE", "obligatoire": True,
                "synonymes": ("echeance", "echeance_id", "id_echeance", "code_echeance",
                              "reference_echeance", "num_echeance"),
            },
            "identifiant_credit": {
                "libelle": "Identifiant du crédit", "type": "TEXTE", "obligatoire": True,
                "synonymes": ("credit", "credit_id", "id_credit", "pret", "loan_id", "numero_credit"),
            },
            "numero": {
                "libelle": "Numéro d'échéance", "type": "NOMBRE", "obligatoire": False,
                "synonymes": ("numero_echeance", "rang", "ordre", "num", "no_echeance", "periode"),
            },
            "date_exigible": {
                "libelle": "Date d'exigibilité", "type": "DATE", "obligatoire": False,
                "synonymes": ("date", "date_echeance", "dt_echeance", "date_prevue", "date_due",
                              "echeance_le", "date_tombee"),
            },
            "montant_du": {
                "libelle": "Montant dû", "type": "MONTANT", "obligatoire": False,
                "synonymes": ("montant", "montant_attendu", "montant_echeance", "mt_du",
                              "montant_a_payer", "traite"),
            },
        },
    },
    "paiements": {
        "libelle": "Paiements",
        "role": "Ce qui a réellement été versé. La plateforme observe ces versements, elle ne les encaisse pas.",
        "champs": {
            "identifiant_paiement": {
                "libelle": "Identifiant du paiement", "type": "TEXTE", "obligatoire": True,
                "synonymes": ("paiement", "paiement_id", "id_paiement", "code_paiement", "reglement",
                              "versement", "num_paiement", "reference_paiement"),
            },
            "identifiant_credit": {
                "libelle": "Identifiant du crédit", "type": "TEXTE", "obligatoire": True,
                "synonymes": ("credit", "credit_id", "id_credit", "pret", "loan_id", "numero_credit"),
            },
            "identifiant_echeance": {
                "libelle": "Identifiant de l'échéance", "type": "TEXTE", "obligatoire": False,
                "synonymes": ("echeance", "echeance_id", "id_echeance", "num_echeance"),
            },
            "date_paiement": {
                "libelle": "Date du versement", "type": "DATE", "obligatoire": False,
                "synonymes": ("date", "date_reglement", "date_versement", "dt_paiement",
                              "date_encaissement", "date_operation"),
            },
            "montant_paye": {
                "libelle": "Montant versé", "type": "MONTANT", "obligatoire": False,
                "synonymes": ("montant", "montant_regle", "montant_verse", "mt_paye", "somme_versee",
                              "montant_encaisse"),
            },
            "canal": {
                "libelle": "Canal de paiement", "type": "TEXTE", "obligatoire": False,
                "synonymes": ("mode", "mode_paiement", "moyen", "moyen_paiement", "type_paiement", "guichet"),
            },
        },
    },
}

ORDRE_TABLES = ("clients", "activites", "demandes_credit", "credits", "echeances", "paiements")


def champs_obligatoires(table):
    return [code for code, champ in TABLES[table]["champs"].items() if champ["obligatoire"]]


def decrire_referentiel():
    """Description destinée à l'écran de correspondance."""
    return [{
        "code": code,
        "libelle": TABLES[code]["libelle"],
        "role": TABLES[code]["role"],
        "champs": [{
            "code": champ_code,
            "libelle": champ["libelle"],
            "type": champ["type"],
            "obligatoire": champ["obligatoire"],
        } for champ_code, champ in TABLES[code]["champs"].items()],
    } for code in ORDRE_TABLES]
