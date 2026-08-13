# CIF — Évaluation du risque de microcrédit

Prototype Django d'aide à la décision pour les agents de microfinance. Il permet de saisir ou charger un dossier fictif, d'estimer un risque avec des règles transparentes et d'expliquer le résultat. La décision d'octroi reste humaine.

> Les données et résultats sont pédagogiques et fictifs. Ne pas utiliser ce prototype pour accorder ou refuser un crédit réel.

## Règle d'architecture

> **Le moteur de calcul ne connaît aucun secteur d'activité, aucun produit de crédit et aucune politique d'octroi. Il exécute uniquement des cadres d'analyse versionnés et configurés par l'institution.**

Cette frontière est ce qui empêche le projet de devenir une accumulation de cas particuliers. Une méthode d'analyse n'est jamais écrite dans le code : elle est décrite par l'institution sous forme de rubriques, de formules et de règles, puis exécutée telle quelle. Trois couches restent séparées :

| Couche | Nature | État |
| --- | --- | --- |
| Moteur de calcul | déterministe : mêmes valeurs et même cadre donnent le même résultat | en place |
| Moteur de règles | interprète les résultats selon des seuils appartenant à l'institution | en place |
| Modèle statistique | appris sur l'historique, produit une probabilité de défaut | non construit |

Une seconde règle borne le périmètre : **si une fonctionnalité ne sert pas directement à acquérir, comprendre, nettoyer, transformer, scorer, expliquer ou surveiller les données de risque de crédit, elle n'entre pas dans le prototype**. Le détail est dans le [périmètre du challenge](documentation/13-perimetre-du-challenge.md).

## Démarrage rapide

Prérequis : Python 3.12 ou plus récent et Git.

```powershell
git clone https://github.com/bahdev223/cif-microcredit-scoring.git
cd cif-microcredit-scoring
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python backend/manage.py migrate
python backend/manage.py runserver
```

Ouvrir [http://127.0.0.1:8000/](http://127.0.0.1:8000/). L'écran charge Fatou au démarrage ; le dossier peut être modifié ou remplacé par un JSON de `donnees/echantillons/`.

## Parcours disponibles

| Besoin | Accès ou commande |
| --- | --- |
| Saisir et analyser un dossier | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) |
| Vérifier l'API | [http://127.0.0.1:8000/api/etat/](http://127.0.0.1:8000/api/etat/) |
| Administrer les dossiers | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) |
| Générer le monde fictif | `python simulation/generer.py` |
| Contrôler les données | `python tests/verifier_monde.py` |
| Contrôler le moteur de cadres | `python tests/test_cadres.py` |

La génération écrit les CSV hors du dépôt, dans `C:\Users\hp\cif-microcredit-donnees-locales\synthetiques\` par défaut. Lancer ensuite les contrôles avant toute publication.

## Organisation

```text
backend/          application Django, API, cadres d'analyse, moteurs et audit
frontend/         écran de démonstration, styles et JavaScript
donnees/          échantillons, données synthétiques et publiques
simulation/       configuration et générateur du monde fictif
laboratoires/     notebooks data science
modeles/          modèles entraînés et registre
documentation/    documentation produit, technique et data
tests/            contrôles automatiques du simulateur
```

Le détail est dans le [guide technique de l'environnement](documentation/08-guide-technique-environnement.md).

## Documentation

- [Index de la documentation](documentation/README.md)
- [Vision produit](documentation/01-vision-produit.md)
- [Règles et données](documentation/02-regles-et-donnees.md)
- [Architecture](documentation/03-architecture-et-evolution.md)
- [Guide de démonstration](documentation/04-guide-demo.md)
- [Contrat API](documentation/05-api.md)
- [Laboratoire synthétique](documentation/06-laboratoire-synthetique.md)
- [Dictionnaire des données synthétiques](documentation/07-dictionnaire-donnees-synthetiques.md)
- [Guide technique : installation, exécution et structure](documentation/08-guide-technique-environnement.md)
- [Guide d'entretien terrain](documentation/12-guide-entretien-terrain.md)
- [Périmètre du challenge](documentation/13-perimetre-du-challenge.md)
- [Données fictives](donnees/README.md)
