# Données

Tous les fichiers de données sont fictifs ou publics et restent séparés du code applicatif.

```text
synthetiques/brutes/     ce que les institutions fictives auraient enregistré
synthetiques/verite/     paramètres cachés du simulateur, interdits à l'entraînement
synthetiques/traitees/   données nettoyées, contrôlées et indicateurs calculés
synthetiques/variables/  dataset final destiné aux laboratoires de scoring
publiques/               jeux de données publics, documentés séparément
echantillons/            petits dossiers à charger dans l'interface ou les tests
```

## La règle la plus importante

`brutes/` est la **seule** source autorisée pour entraîner un modèle. `verite/` contient ce que le simulateur sait et qu'aucune institution réelle ne saurait : la personnalité financière des clients, leur trajectoire économique mois par mois, et ce qui serait arrivé aux demandes refusées. Un laboratoire qui lirait ces fichiers ne mesurerait plus rien.

Les fichiers sont numérotés par ordre de génération, dans les deux dossiers : `01_institutions.csv` est observable, `08_situations_mensuelles.csv` ne l'est pas. Le numéro dit l'ordre, le dossier dit la visibilité.

## Parcours des données

`simulation/` produit les tables brutes. `simulation/nettoyer_donnees.py` transforme les dossiers de démonstration en données traitées. Les futurs laboratoires construiront ensuite `synthetiques/variables/scoring_credit.csv` sans utiliser d'information future.

Les fichiers sous `synthetiques/brutes` doivent rester reproductibles et ne doivent jamais être modifiés manuellement. Git conserve l'historique de toutes les versions suivies.

Le contrat du dossier chargeable est disponible dans `echantillons/schema_dossier_saisie.json`.

Les tables des cinq institutions fictives sont décrites colonne par colonne dans `documentation/07-dictionnaire-donnees-synthetiques.md`. Les fichiers JSON de démonstration restent dans `echantillons/` : ils ne font pas partie des tables brutes.
