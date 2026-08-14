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

## Deux niveaux de données

| Niveau | Statut | Exemples |
| --- | --- | --- |
| Schéma canonique | imposé par la plateforme | client, demande, crédit, échéance, paiement, produit, date, montant |
| Cadres d'analyse institutionnels | configurable | recettes commerciales, stock, charges de transport, surface agricole, campagne, production |

Le schéma canonique assure l'interopérabilité et les calculs communs. Les cadres ajoutent le contexte métier sans rendre tout le système arbitrairement configurable.

Les features canoniques — ancienneté relation, nombre de crédits, crédits soldés, retard maximal et fréquence des retards — sont dérivées du Data Mart. Les features métier — marge disponible, pression de remboursement, saisonnalité — proviennent des cadres. Le laboratoire décide ensuite lesquelles sont scientifiquement recevables pour un modèle.

## Fiche de gouvernance par champ

Chaque champ ajouté doit préciser :

```text
nom · description · type · obligatoire ? · source possible
donnée personnelle ? · donnée sensible ? · opération justifiée
usage : identification / analyse métier / feature candidate / outcome / audit
FEATURE_SCORING : false par défaut · conservation : à définir
```

## Contrat minimal d'un connecteur

Chaque connecteur ou mapping d'institution doit déclarer :

```text
institution source · version · format entrant (CSV / XLSX / API)
entité cible · colonne ou chemin source · champ canonique
transformation · type attendu · règle de validation
traitement si absent · statut actif · journal des rejets
```

Il ne définit ni règle de scoring ni écriture directe dans les tables métier. Son seul rôle est de transformer une source institutionnelle en données canoniques vérifiables.

## Données exclues par défaut

Sont exclues sans justification exceptionnelle : religion, ethnie, opinions politiques, orientation sexuelle, contacts, SMS, réseaux sociaux personnels, historique web, géolocalisation permanente et photos non nécessaires.

Les données comme le sexe, l'âge, la localité ou la situation familiale peuvent exister dans une source mais ne sont jamais des features activées par défaut.

## Prochaine décision

Avant de coder une API d'ingestion, valider ce contrat avec les institutions rencontrées : noms de colonnes disponibles, clés de rapprochement, dates fiables, définitions de retard et de défaut, règles de conservation et accès autorisés.

## Métadonnées de fiabilité

Pour les données susceptibles d'être utilisées analytiquement, prévoir lorsque disponible : `date_observation`, `source_donnee`, `mode_collecte` et `statut_verification`. Cette traçabilité permet de différencier une valeur transactionnelle, documentaire, saisie par agent ou auto-déclarée, sans confondre la provenance avec la valeur elle-même.
