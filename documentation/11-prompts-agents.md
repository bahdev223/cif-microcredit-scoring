# Prompts prêts à remettre aux agents

Les prompts ci-dessous sont prêts à copier. Donner à chaque agent le dépôt, son périmètre et le [guide de travail](10-guide-agents.md).

## Prompt maître — Agent 01 Architecture et fondation

```text
Tu travailles sur le dépôt cif-microcredit-scoring.

Lis d'abord documentation/10-guide-agents.md, le README et la documentation existante.

Contexte : projet Challenge 2 — Scoring Microcrédit du Hackathon CIF DigiCoop-WA+ 2026. Nous construisons le laboratoire et le prototype, pas un modèle de machine learning.

Objectif : auditer l'état actuel, produire une structure cible, identifier les écarts et proposer un ordre d'implémentation simple pour représenter cinq institutions fictives, stocker des CSV synthétiques indépendants, importer des CSV, contrôler leur qualité, nettoyer et explorer les données.

Interdictions absolues : aucun modèle de scoring ; aucune régression logistique, XGBoost, LightGBM, Random Forest, SHAP, score arbitraire, probabilité de défaut, seuil de décision ou décision automatique de crédit. Ne crée aucune règle microfinance non documentée.

Conserver backend/, frontend/, laboratoires/, donnees/, simulation/, modeles/, documentation/ et tests/. modeles/ est réservé : ne rien y implémenter.

Livrables avant tout changement massif :
1. audit de l'existant ;
2. structure cible ;
3. existant / manquant ;
4. ordre d'implémentation ;
5. risques de régression ;
6. tests nécessaires.

Ne réécris pas du code fonctionnel sans justification. Reste simple. Indique les fichiers consultés, les fichiers modifiés, les contrôles effectués et les limites. Ne commit/push pas.
```

## Prompt — Agent 02 Données synthétiques / SFD fictives

```text
Tu es responsable exclusivement du laboratoire de données synthétiques du projet cif-microcredit-scoring.

Lis documentation/10-guide-agents.md, documentation/07-dictionnaire-donnees-synthetiques.md et donnees/README.md.

Mission : construire et documenter cinq institutions de microfinance fictives indépendantes, environ 50 clients chacune. Les données ne prétendent pas représenter statistiquement le Mali ou une SFD réelle.

Produis séparément clients.csv, activites.csv, demandes_credit.csv, credits.csv, echeances.csv et paiements.csv. Respecte les relations et la cohérence temporelle : une échéance ne précède pas un décaissement, un paiement ne référence pas un crédit absent, aucune information future ne se trouve dans un dossier passé.

Un client peut ne jamais demander, être refusé, avoir plusieurs crédits successifs, des paiements normaux, retards, paiements partiels et régularisations. Ajoute quelques personnages pédagogiques déterministes, notamment Fatou, traçable dans les six fichiers. Prévois aussi les scénarios de qualité documentés : champs manquants et incohérences destinées au moteur de qualité.

Interdictions : aucun ML, scoring, régression, SHAP, moteur de décision ou règle « si X alors défaut ». Utilise une graine configurable et documente toutes les hypothèses.

Avant de générer massivement : définir et documenter les schémas, types, colonnes obligatoires, relations et règles structurelles. Les CSV doivent rester importables indépendamment dans l'application. Exécute python tests/verifier_monde.py. Ne commit/push pas.
```

## Prompt — Agent 03 Import CSV et Data Quality

```text
Tu es responsable du module Import CSV et Qualité des données du projet cif-microcredit-scoring.

Lis documentation/10-guide-agents.md, documentation/05-api.md et backend/api/views.py. Tu ne travailles pas sur le scoring et ne développes aucun algorithme de prédiction.

Objectif : permettre à une institution de déposer clients.csv, activites.csv, demandes_credit.csv, credits.csv, echeances.csv et paiements.csv, puis d'obtenir un rapport avant tout import.

Architecture obligatoire :
lecture CSV → validation structurelle → validation relationnelle → rapport qualité → aperçu → confirmation explicite → persistance → traçabilité.

Contrôles : encodage, séparateur, en-têtes, colonnes obligatoires, types, identifiants uniques, valeurs manquantes, doublons, dates, références inexistantes et incohérences structurelles.

Classer chaque problème :
- ERREUR : bloque la ligne ou l'import ;
- AVERTISSEMENT : valeur inhabituelle à vérifier ;
- INFORMATION : non bloquant.

Ne corrige jamais silencieusement une donnée métier. Affiche fichiers reconnus, lignes, lignes valides/problématiques, erreurs, avertissements, complétude et aperçu. Le détail des anomalies est visible avant confirmation.

Prévoir la traçabilité : institution, fichier, date, statut, nombres de lignes, lignes importées/rejetées, erreurs, avertissements et utilisateur si authentifié.

Écrire des validateurs testables et des fixtures : CSV valide, colonne absente, mauvais type, doublon, référence client absente, date incohérente, valeur manquante, fichier vide et lot partiellement invalide.

Avant remise : python backend/manage.py check, python backend/manage.py test api, git diff --check. Mettre à jour la documentation API et OpenAPI si des routes changent. Ne commit/push pas.
```

## Prompts courts — Agents 04 à 09

### Agent 04 Backend métier

```text
Lis documentation/10-guide-agents.md. Travaille exclusivement sur les modèles, migrations, API, rôles et audit du backend. Crée des fonctionnalités pour Clients, Demandes, Crédits, Remboursements et Audit sans casser les contrats API. Ajoute les tests correspondants, mets à jour OpenAPI et ne fais aucun scoring. Ne commit/push pas.
```

### Agent 05 Frontend / UX

```text
Lis documentation/10-guide-agents.md et documentation/05-api.md. Travaille uniquement dans frontend/. Construis une interface métier claire, responsive et accessible : dashboard, clients, demandes, crédits, remboursements, audit, import et configuration. Toutes les données proviennent de l'API ; aucun contenu métier codé en dur. Vérifie node --check et ne commit/push pas.
```

### Agent 06 Data / statistiques

```text
Lis documentation/10-guide-agents.md. Travaille dans laboratoires/ et documentation/. Fais uniquement exploration, statistiques descriptives, qualité, préparation des variables et risques de fuite. Ne lis pas les données cachées, ne construis aucun modèle de scoring et ne modifies pas backend/ ou frontend/. Ne commit/push pas.
```

### Agent 07 Scoring / modèles

```text
Le module Scoring est volontairement gelé. N'implémente aucun modèle, aucune règle de score, aucune explicabilité SHAP et aucune décision de crédit. Lis la documentation, liste seulement les prérequis data et métier nécessaires avant de démarrer une phase de modélisation. Ne commit/push pas.
```

### Agent 08 QA / non-régression

```text
Lis documentation/10-guide-agents.md. Travaille uniquement sur les tests et fixtures. Couvre Clients, Demandes, Crédits, Remboursements, Audit, Import, Configuration et Dashboard. N'ajoute aucune fonctionnalité produit. Exécute python backend/manage.py test et remets les scénarios couverts/non couverts. Ne commit/push pas.
```

### Agent 09 Documentation

```text
Lis documentation/10-guide-agents.md. Travaille dans documentation/ et README. Clarifie les contrats CSV, API, installation, rôles, Docker, limites et parcours métier. Ne modifie pas le code sauf un lien manifestement cassé. Ne commit/push pas.
```

