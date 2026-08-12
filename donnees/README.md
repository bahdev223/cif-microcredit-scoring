# Données du laboratoire

Les données restent dans ce dépôt, au même titre que le code, mais elles sont séparées par étape de travail. Elles sont toutes fictives et versionnées par Git : chaque modification est traçable, comparable et réversible avec un commit.

```text
donnees/
├── brutes/       # données telles que créées par le simulateur ; on ne les modifie pas à la main
├── nettoyees/    # copie contrôlée après vérification et normalisation
├── scenarios/    # dossiers uniques chargeables dans l'interface de démonstration
├── schemas/      # contrat des colonnes/champs attendus
└── temporaires/  # fichiers locaux jetables, ignorés par Git
```

## Utilisation

- Charger un scénario dans l'écran de saisie : `donnees/scenarios/cas_fatou.json`.
- Utiliser `donnees/brutes/dossiers_demo.json` comme entrée de test en lot.
- Utiliser `donnees/nettoyees/dossiers_demo_nettoyes.json` après les contrôles de base.
- Ne pas modifier directement le dossier `brutes/` : créer une nouvelle version du générateur ou du scénario.

Les fichiers sous `brutes`, `nettoyees`, `scenarios` et `schemas` sont suivis par Git. Le dossier `temporaires` ne l'est pas, afin de ne pas envoyer de fichiers d'essai inutiles.

## Retour à une version antérieure

Git garde l'historique. Pour retrouver une ancienne version d'un fichier :

```powershell
git log -- donnees/scenarios/cas_fatou.json
git restore --source <identifiant_commit> -- donnees/scenarios/cas_fatou.json
```

Ne jamais utiliser ces données pour une décision réelle ou comme preuve de performance en production.
