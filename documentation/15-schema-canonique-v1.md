# Schéma canonique V1

## But

Ce document définit le contrat minimal commun aux imports CSV, Excel et à la future API d'ingestion. Il sert au mapping des institutions ; ce n'est ni un modèle KYC réglementaire, ni une liste de variables à envoyer au scoring.

## Règles fondatrices

1. L'identité sert à rattacher le dossier, pas à prédire le risque.
2. La minimisation s'applique : chaque champ doit avoir un usage justifié.
3. `FEATURE_SCORING = false` par défaut.
4. Les données postérieures à une décision sont des outcomes, jamais des informations disponibles à T0.
5. CSV, Excel et API traversent le même pipeline de mapping, validation, qualité, normalisation et persistance.

## Entités minimales

| Entité | Champs minimaux | Rôle principal |
| --- | --- | --- |
| Institution | `institution_id`, nom affiché | provenance et isolement logique |
| Client | `institution_id`, `client_id_source`, `nom_affichage`, `date_adhesion`, `statut_client` | rattachement et ancienneté relationnelle |
| Activité | `client_id_source`, secteur, type, ancienneté si connue | contexte économique |
| Demande | `client_id_source`, montant, durée, objet, date | analyse à T0 |
| Crédit | `credit_id_source`, `client_id_source`, montant, durée, date, statut | historique de crédit |
| Échéance | `echeance_id_source`, `credit_id_source`, date exigible, montant dû | calendrier attendu |
| Paiement | `paiement_id_source`, `credit_id_source`, date, montant | comportement observé |
| Situation économique | client, date de collecte, cadre, rubriques et valeurs | collecte interne à T0 |

Le `nom_affichage` peut être remplacé par un pseudonyme dans un jeu analytique. Le rapprochement technique utilise les identifiants source et institutionnels, jamais un nom comme clé principale.

## Fiche de gouvernance par champ

Chaque champ ajouté doit préciser :

```text
nom · description · type · obligatoire ? · source possible
donnée personnelle ? · donnée sensible ? · opération justifiée
usage : identification / analyse métier / feature candidate / outcome / audit
FEATURE_SCORING : false par défaut · conservation : à définir
```

## Données exclues par défaut

Sont exclues sans justification exceptionnelle : religion, ethnie, opinions politiques, orientation sexuelle, contacts, SMS, réseaux sociaux personnels, historique web, géolocalisation permanente et photos non nécessaires.

Les données comme le sexe, l'âge, la localité ou la situation familiale peuvent exister dans une source mais ne sont jamais des features activées par défaut.

## Prochaine décision

Avant de coder une API d'ingestion, valider ce contrat avec les institutions rencontrées : noms de colonnes disponibles, clés de rapprochement, dates fiables, définitions de retard et de défaut, règles de conservation et accès autorisés.
