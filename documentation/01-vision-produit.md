# Vision produit

## Probleme

L'agent de credit doit analyser des dossiers parfois incomplets, avec peu d'historique formel. L'analyse peut etre longue et heterogene d'un agent a l'autre.

## Utilisateur

Agent ou responsable de credit d'une institution de microfinance.

## Promesse du prototype

L'agent consolide la situation actuelle du demandeur avec son historique importé, obtient une estimation de risque explicable, des points à vérifier et des règles métier visibles. Le système n'accorde ni ne refuse automatiquement un crédit.

## Définition officielle

> **CIF est une infrastructure de décision de crédit pilotée par les données de l'institution.**

Elle intègre les historiques existants par CSV, Excel puis API, les mappe vers un schéma commun, qualifie leur qualité, complète les informations nécessaires lors de l'instruction, construit des variables analytiques, permet de développer et surveiller un modèle propre au portefeuille, puis restitue une analyse explicable à l'humain.

Ce n'est ni un ERP de microfinance, ni un formulaire de crédit isolé, ni un modèle universel prétendant connaître toutes les institutions.

## Deux sources, un seul dossier

| Source | Origine | Rôle |
| --- | --- | --- |
| Collecte interne T0 | formulaire dynamique saisi par l'agent | décrire la situation actuelle : recettes, charges, engagements, activité |
| Historique importé | CSV, Excel puis API depuis le SI de l'institution | comprendre les crédits passés, échéances, paiements et retards |

Les deux sources sont conservées séparément puis rapprochées dans le dossier consolidé. Aucune importation ne doit écraser la collecte interne.

## Parcours Fatou

1. L'agent saisit le dossier de Fatou.
2. Il lance l'analyse.
3. Il lit le niveau de risque et les facteurs.
4. Il simule une baisse du montant demande si necessaire.
5. Il prend et justifie lui-meme sa decision.

## Hors périmètre

Le prototype ne remplace pas le logiciel de microfinance : pas d'encaissement, de décaissement réel, de caisse, de comptabilité, de clôture ni de gestion transactionnelle des paiements. Les paiements et échéances sont lus, importés et analysés comme historique de risque. Le modèle statistique, les connecteurs spécifiques et les données réelles ne viennent qu'après validation métier, disponibilité légale des données et évaluation contrôlée.
