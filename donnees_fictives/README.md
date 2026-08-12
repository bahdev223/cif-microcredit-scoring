# Données fictives chargeables

Ces fichiers JSON sont séparés du code et contiennent exclusivement des données de démonstration.

- `cas_fatou.json` : un dossier unique, directement chargeable dans l'écran de saisie.
- `dossiers_demo.json` : une liste de dossiers servant de base à de futurs tests en lot. Le premier dossier peut être chargé dans l'écran actuel.

L'interface accepte un objet JSON unique ayant les mêmes clés que `cas_fatou.json`. Elle refuse volontairement une liste pour éviter de charger silencieusement le mauvais dossier.

Ces données ne sont ni réelles ni représentatives d'une institution partenaire. Elles ne doivent pas être utilisées pour entraîner ou valider un modèle de production.
