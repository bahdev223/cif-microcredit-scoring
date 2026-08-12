# Laboratoire synthétique de microfinance

## Statut et limite

Ce laboratoire représente une SFD fictive. Les données qui en sortiront serviront à développer, tester et démontrer le pipeline technique. Elles ne prouvent pas qu'un modèle prédit le défaut au Mali ou dans une institution réelle.

Le simulateur est séparé du produit Django et du moteur d'évaluation du risque. Il crée un monde fictif ; l'application de scoring ne doit utiliser que les observations historiques qu'il produit.

## SFD fictive : Kènèya Finance

| Élément | Valeur de démonstration |
| --- | --- |
| Nom | Kènèya Finance (fictif) |
| Pays de démonstration | Mali (fictif, sans représenter une institution réelle) |
| Période simulée | Janvier 2023 à décembre 2026 |
| Agences | Bamako Centre, Sikasso, Ségou, Koulikoro |
| Effectif | 12 agents de crédit répartis entre les agences |
| Population initiale | 500 clients synthétiques |

## Produits de crédit

| Code | Produit | Montant indicatif | Durée | Public |
| --- | --- | --- | --- | --- |
| STOCK | Fonds de roulement | 50 000 à 600 000 FCFA | 3 à 12 mois | Commerce et artisanat |
| AGRI | Campagne agricole | 100 000 à 800 000 FCFA | 6 à 12 mois | Agriculture |
| EQUIPEMENT | Petit équipement | 150 000 à 1 000 000 FCFA | 12 à 24 mois | Activités établies |

Les bornes sont des paramètres du simulateur et non une politique réelle de crédit.

## Profils clients à représenter

- Commerçants réguliers, commerçants à forte activité mais faible marge, artisans, agriculteurs saisonniers et prestataires de services.
- Nouveaux clients sans historique, bons payeurs, retards occasionnels et incidents récurrents.
- Clients déjà endettés, activités anciennes à faible marge, revenus irréguliers et dossiers partiellement renseignés.
- Cas pièges : fort chiffre d'affaires sans capacité de remboursement, marge saine avec faible chiffre d'affaires, historique absent, ou données incohérentes.

Un client peut déposer plusieurs demandes et avoir une trajectoire dans le temps. Une ligne de dataset ne représente donc pas un client entier.

## Cycle temporel

```text
Client → demande → décision simulée → crédit → échéancier → paiements/incidents → résultat observé
```

Une demande est datée. Les caractéristiques utilisées pour la décision sont celles connues à cette date. Aucun paiement futur ni résultat final ne doit être utilisé comme variable de scoring : cela éviterait une fuite d'information.

## Modèle de données à générer

| Table | Clé | Rôle | Exemples de champs |
| --- | --- | --- | --- |
| `agences` | `agence_id` | Implantations fictives | nom, ville, date_ouverture |
| `agents_credit` | `agent_id` | Agents fictifs | agence_id, ancienneté_mois |
| `produits_credit` | `produit_id` | Paramètres de produits | code, montant_min, montant_max, durée_min, durée_max |
| `clients_synthetiques` | `client_id` | Profil stable du client | agence_id, secteur, date_entree, profil_synthetique |
| `activites_economiques` | `activite_id` | Situation économique datée | client_id, mois, chiffre_affaires, charges_activite, saisonnalité |
| `demandes_credit_synthetiques` | `demande_id` | Dossier à la date de demande | client_id, agent_id, produit_id, date_demande, montant, durée, données_connues |
| `decisions_simulees` | `decision_id` | Résultat de l'étude fictive | demande_id, statut, motif_simulé |
| `credits_synthetiques` | `credit_id` | Crédit accepté et décaissé | demande_id, date_decaissement, montant, durée, échéance |
| `echeances_synthetiques` | `echeance_id` | Calendrier attendu | credit_id, numéro, date_exigible, montant_dû |
| `paiements_synthetiques` | `paiement_id` | Événements de remboursement | échéance_id, date_paiement, montant_payé, jours_retard |
| `resultats_credit_synthetiques` | `credit_id` | Cible observée après le crédit | statut_final, défaut_expérimental, jours_retard_max |

Les identifiants seront pseudonymes et sans données personnelles réelles.

## Définition expérimentale du défaut

Pour le laboratoire, un crédit sera considéré en défaut expérimental si l'une de ces conditions est observée à la fin de la période d'observation :

- solde impayé avec au moins 90 jours de retard ; ou
- abandon simulé de remboursement ; ou
- restructuration simulée pour impayé persistant.

Cette définition est une étiquette expérimentale. Elle devra être validée et remplacée par la définition métier/réglementaire de la SFD partenaire avant toute utilisation réelle.

## Principes du futur simulateur

1. Construire d'abord les entités et les historiques, puis les demandes, crédits, échéances et paiements.
2. Produire les incidents au moyen d'une probabilité synthétique incluant économie, historique, saisonnalité, événements latents et bruit aléatoire contrôlé.
3. Ne pas coder une règle directe du type « retards élevés = défaut certain ».
4. Conserver une graine aléatoire documentée afin de reproduire une démonstration.
5. Prévoir des données manquantes et incohérentes identifiées comme telles.
6. Séparer les paramètres internes du simulateur des colonnes données au futur modèle de scoring.

## Livrables de la prochaine étape

Avant toute génération :

1. Valider ce dictionnaire de données avec l'équipe.
2. Fixer les distributions des secteurs, produits, montants et durées.
3. Définir les scénarios économiques et saisonniers.
4. Écrire les tests de cohérence : aucun paiement avant décaissement, aucune échéance hors durée, aucune information future dans une demande.
5. Seulement ensuite écrire le générateur et créer le dataset synthétique versionné.
