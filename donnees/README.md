# Données

Tous les fichiers de données sont fictifs ou publics et restent séparés du code applicatif.

```text
synthetiques/brutes/     sorties brutes du futur simulateur, jamais modifiées à la main
synthetiques/traitees/   données nettoyées et contrôlées
synthetiques/variables/  dataset final destiné aux laboratoires de scoring
publiques/               jeux de données publics, documentés séparément
echantillons/            petits dossiers à charger dans l'interface ou les tests
```

## Parcours des données

`simulation/` produit les tables brutes. `simulation/nettoyer_donnees.py` transforme les dossiers de démonstration en données traitées. Les futurs laboratoires construiront ensuite `synthetiques/variables/scoring_credit.csv` sans utiliser d'information future.

Les fichiers sous `synthetiques/brutes` doivent rester reproductibles et ne doivent jamais être modifiés manuellement. Git conserve l'historique de toutes les versions suivies.

Le contrat du dossier chargeable est disponible dans `echantillons/schema_dossier_saisie.json`.

Les neuf tables CSV de la SFD fictive sont décrites colonne par colonne dans `documentation/07-dictionnaire-donnees-synthetiques.md`. Les fichiers JSON de démonstration restent dans `echantillons/` : ils ne font pas partie des tables brutes de la SFD.
