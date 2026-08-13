# Périmètre du challenge

Ce document existe pour empêcher une dérive précise : construire par accident un ERP de microfinance au lieu d'une solution de scoring.

## La règle

> **Si une fonctionnalité ne sert pas directement à acquérir, comprendre, nettoyer, transformer, scorer, expliquer ou surveiller les données de risque de crédit, elle n'entre pas dans le prototype du challenge.**

Elle se lit dans les deux sens. Récupérer et préparer les données n'est pas une dérive : sans données, il n'y a pas d'analyse statistique sérieuse, donc pas de challenge. Mais exécuter les opérations de l'institution n'est pas notre affaire.

## La chaîne

```text
DONNÉES DE L'INSTITUTION
          ↓
   ACQUISITION        CSV · Excel · API · saisie du dossier
          ↓
   MAPPING            colonnes de l'institution → référentiel interne
          ↓
   DATA QUALITY       présence, type, cohérence, dates, historique
          ↓
   CADRE D'ANALYSE    rubriques, formules, règles configurées
          ↓
   FEATURE ENGINE     variables métier
          ↓
   STATISTICAL ENGINE probabilité de défaut
          ↓
   EXPLICATION → SIMULATION → DÉCISION HUMAINE
```

Ces cinq couches ne doivent jamais être confondues. La source dit d'où vient la donnée ; le mapping dit à quoi elle correspond ; la qualité dit si on peut lui faire confiance ; la variable dit ce qu'on en dérive ; le modèle dit ce que l'historique permet d'estimer.

## Ce qui entre

Import CSV et Excel, API d'import, mapping des colonnes, contrôles de qualité, saisie du dossier au moment de la demande, constructeur de cadres d'analyse, Feature Engine, historique des crédits et des remboursements, moteur statistique, explicabilité, simulation, gestion de l'incertitude et du client sans historique, versionnement des modèles, audit des analyses, surveillance du modèle.

## Ce qui entre, mais minimal

| Sujet | Ce qui est utile | Ce qui serait une dérive |
| --- | --- | --- |
| Clients | identité minimale, activités, historique | CRM, prospects, campagnes, segmentation commerciale, fidélisation |
| Produits de crédit | montants, durées, cadre d'analyse associé | moteur commercial complet de produits financiers |
| Documents | pièces nécessaires au dossier | GED, signatures, workflows documentaires, archivage légal, OCR massif |
| Échéances et paiements | l'historique qui produit le résultat observé | caisse réelle, encaissement, comptabilisation |

La distinction tient en une phrase : le système **observe, importe et structure** l'historique du crédit ; il ne devient pas le système transactionnel qui exécute la microfinance.

## Ce qui n'entre pas

**Un core banking.** Comptes d'épargne, dépôts, retraits, caisse, transferts, comptabilité, trésorerie, clôtures. Ce n'est plus une solution de scoring, c'est une banque.

**Le cycle opérationnel complet d'une institution.** Représenter demande → décision → crédit → remboursement est nécessaire, parce que c'est ce qui produit les données. L'exécuter réellement ne l'est pas.

**Un constructeur universel de formulaires.** Le constructeur de cadres d'analyse s'arrête aux sections, rubriques, calculs, règles et mapping. Pas de workflow, pas de signatures, pas d'automatisations, pas de permissions par champ.

**Le constructeur comme innovation principale.** Ce n'est pas la démonstration ; c'est le moyen de dire que le moteur s'adapte aux données et aux méthodes de chaque institution. Il doit immédiatement alimenter le Feature Engine, puis le modèle, puis le risque.

**Deux cents règles inventées avant le terrain.** Quelques règles expérimentales clairement identifiées, puis la question : montrez-nous les vôtres.

**Un modèle statistique avant les données.** L'infrastructure peut se construire et s'expérimenter sur données publiques ou synthétiques. Annoncer une prédiction de défaut sans jeu de données approprié serait injustifiable.

**Cinquante sources alternatives.** Mobile money, téléphonie, réseaux sociaux, GPS, tontines. Chacune demande accès, consentement, qualité, légitimité, mapping et validation prédictive. On commence par les données que les institutions possèdent déjà — c'est probablement le meilleur avantage disponible.

## Les trois portes d'acquisition

| Porte | État | Rôle |
| --- | --- | --- |
| A — CSV et Excel | contrôle des fichiers en place, mapping à construire | reprendre l'historique existant |
| B — Saisie du dossier | en place, à brancher sur les cadres | recueillir ce qui n'existe pas dans l'historique |
| C — API | prévue, non développée | connecter le système d'information plus tard |

Aucun connecteur spécifique ne sera écrit avant de savoir ce que l'institution utilise réellement.
