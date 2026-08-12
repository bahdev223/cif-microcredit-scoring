# Interface de démonstration

Cette interface est servie par Django à l'adresse `http://127.0.0.1:8000/`. Elle permet de tester un dossier fictif complet sans outil externe.

## Ce que l'on peut faire

1. Charger le cas Fatou prérempli ou importer un fichier JSON compatible depuis `../donnees/echantillons/`.
2. Corriger les données d'activité, du ménage et de l'historique dans le formulaire.
3. Visualiser les calculs intermédiaires avant l'envoi.
4. Analyser le dossier et lire le score, la recommandation, les indicateurs et les règles déclenchées.
5. Tester un montant réduit de 20 % depuis le résultat.

## Fichiers

| Chemin | Rôle |
| --- | --- |
| `templates/index.html` | structure et textes de l'écran |
| `static/styles.css` | mise en page et adaptation mobile |
| `static/app.js` | chargement JSON, calculs visibles et appel API |

Le contrat du fichier importable est dans `../donnees/echantillons/schema_dossier_saisie.json`. Les champs attendus sont détaillés dans [le contrat API](../documentation/05-api.md).

