# CIF — Évaluation du risque de microcrédit

Prototype Django d'aide à la décision pour les agents de microfinance. Il permet de saisir ou charger un dossier fictif, d'estimer un risque avec des règles transparentes et d'expliquer le résultat. La décision d'octroi reste humaine.

> Les données et résultats sont pédagogiques et fictifs. Ne pas utiliser ce prototype pour accorder ou refuser un crédit réel.

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

La génération réécrit les CSV sous `donnees/synthetiques/`. Lancer ensuite les contrôles avant toute publication.

## Organisation

```text
backend/          application Django, API, règles et audit
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
- [Données fictives](donnees/README.md)

