# Simulation — le monde fictif

Ce dossier contient le générateur reproductible de cinq institutions de microfinance fictives. Il ne fait pas partie du produit Django, et ses règles internes ne doivent jamais être utilisées directement par le moteur de scoring : le simulateur fabrique un monde, le modèle doit l'apprendre de l'extérieur.

Le contrat complet — chaque table, chaque colonne, chaque loi de génération — est dans `documentation/07-dictionnaire-donnees-synthetiques.md`. Ce README ne dit que comment s'en servir.

## Cinq institutions, cinq environnements

| Identifiant | Portefeuille | Ce qu'il sert à éprouver |
| --- | --- | --- |
| `INS-001` | commerce urbain | cycles courts, données propres |
| `INS-002` | agriculture rurale | saisonnalité, chocs sectoriels, données sales |
| `INS-003` | artisans et TPE | durées longues, octroi exigeant |
| `INS-004` | généraliste | référence de calibration |
| `INS-005` | portefeuille difficile | croissance agressive, clientèle fragile |

La question du laboratoire : un même moteur de scoring s'adapte-t-il à ces cinq mondes, ou n'apprend-il que celui qui l'a vu naître ?

## Générer

```powershell
python simulation/generer.py
```

La génération est déterministe : même configuration et même graine donnent les mêmes fichiers, octet pour octet. La graine se remplace en ligne de commande :

```powershell
python simulation/generer.py --graine 7
```

Chaque exécution écrit `donnees/synthetiques/verite/manifeste_generation.json` : graine, version du référentiel, commit du code, nombre de lignes et empreinte SHA-256 de chaque fichier produit. C'est ce manifeste qui permet de vérifier qu'un jeu de données est bien celui qu'on croit.

## Deux sorties, deux statuts

```text
donnees/synthetiques/brutes/   ce que l'institution aurait enregistré  -> entraînement autorisé
donnees/synthetiques/verite/   les paramètres cachés du simulateur     -> entraînement interdit
```

## Contrôler le monde produit

```powershell
python tests/verifier_monde.py
```

Le script vérifie les invariants du dictionnaire : intégrité référentielle, cohérence de l'institution le long de la chaîne, chronologie des dossiers, échéanciers équilibrés, étanchéité des deux mondes, et absence d'information postérieure à la date de décision. Un monde qui échoue ici ne doit pas être publié.

## État d'avancement

Les quatorze couches sont implémentées, ainsi que la dégradation volontaire des données. Restent à faire :

- les cas dorés (`configuration/personnages.yaml`), dont Fatou, Ibrahim et Awa ;
- la question du taux d'intérêt, aujourd'hui nul faute de paramètre défendable ;
- le passage à l'échelle : cinq institutions à 10 000 clients, et le choix du format de stockage pour les 2,4 millions de situations mensuelles.

Les modules `generateurs/clients.py`, `activites.py`, `demandes_credit.py`, `credits.py` et `remboursements.py` datent de la version à institution unique et à tirages indépendants. Ils ne sont plus appelés et peuvent être supprimés.

## Configuration

`configuration/institutions.yaml` décrit les cinq institutions : leur identité observable, et les paramètres latents qui font la différence entre leurs portefeuilles. C'est le fichier qu'on modifie pour changer le monde — jamais les CSV produits, qui sont réécrits à chaque génération.
