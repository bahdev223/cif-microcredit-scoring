# Données

Tous les fichiers de données sont fictifs ou publics et restent séparés du code applicatif.

```text
synthetic/raw/       sorties brutes du futur simulateur, jamais modifiées à la main
synthetic/processed/ données nettoyées et contrôlées
synthetic/features/  dataset final destiné aux notebooks de scoring
public/               jeux de données publics, documentés séparément
samples/              petits dossiers à charger dans l'interface ou les tests
```

## Parcours des données

`simulation/` produit les tables brutes. `simulation/nettoyer_donnees.py` transforme les dossiers de démonstration en données nettoyées. Les futurs notebooks construiront ensuite `synthetic/features/credit_scoring.csv` sans utiliser d'information future.

Les fichiers sous `synthetic/raw` doivent rester reproductibles et ne doivent jamais être modifiés manuellement. Git conserve l'historique de toutes les versions suivies.

Le contrat du dossier chargeable est disponible dans `samples/schema_dossier_saisie.json`.
