# Vision produit

## Probleme

L'agent de credit doit analyser des dossiers parfois incomplets, avec peu d'historique formel. L'analyse peut etre longue et heterogene d'un agent a l'autre.

## Utilisateur

Agent ou responsable de credit d'une institution de microfinance.

## Promesse de la V0

En quelques champs, l'agent obtient une estimation de risque explicable, des points a verifier et des regles metier visibles. Le systeme n'accorde ni ne refuse automatiquement un credit.

## Parcours Fatou

1. L'agent saisit le dossier de Fatou.
2. Il lance l'analyse.
3. Il lit le niveau de risque et les facteurs.
4. Il simule une baisse du montant demande si necessaire.
5. Il prend et justifie lui-meme sa decision.

## Hors perimetre V0

Pas de donnees reelles, d'API bancaire, d'identification client, de modele machine learning ni de decision automatique. Ces elements seront ajoutes seulement apres validation metier et disponibilite de donnees legales.
