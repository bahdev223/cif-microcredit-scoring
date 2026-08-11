# CIF Microcredit Scoring

Prototype V0 d'aide a la decision pour un agent de microfinance. Il analyse un dossier client, estime un niveau de risque et explique clairement les facteurs pris en compte. La decision de credit reste toujours humaine.

## Lancer le prototype

Ce prototype ne depend d'aucun serveur ni installation.

1. Ouvrir `index.html` dans un navigateur.
2. Completer le dossier de Fatou (ou modifier les champs).
3. Cliquer sur **Analyser le dossier**.
4. Lire le risque, les facteurs, la qualite des donnees et les regles declenchees.

## Contenu de cette V0

- formulaire de demande de microcredit;
- estimation transparente du risque, basee sur des regles simples;
- explication des facteurs positifs et negatifs;
- controle de qualite des donnees;
- simulation d'un montant de credit;
- historique de decisions dans le navigateur.

## Documentation

- [Vision produit](docs/01-vision-produit.md)
- [Regles et donnees](docs/02-regles-et-donnees.md)
- [Architecture et evolution](docs/03-architecture-et-evolution.md)
- [Guide de demonstration](docs/04-guide-demo.md)

## Limite importante

Cette V0 est une demo de hackathon avec des donnees fictives et des regles pedagogiques. Elle ne doit pas servir a accorder ou refuser un credit reel avant validation metier, juridique, statistique et securitaire.
