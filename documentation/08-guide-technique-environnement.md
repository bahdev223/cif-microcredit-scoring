# Guide technique de l'environnement

Ce guide explique comment installer, exécuter et maintenir le prototype CIF. Il s'adresse à une personne qui vient de cloner le dépôt et veut reproduire la démonstration ou travailler sur les données synthétiques.

## 1. Prérequis

- Windows avec PowerShell ;
- Python 3.12 ou plus récent (`python --version`) ;
- Git pour cloner et publier le dépôt ;
- Docker Desktop est facultatif, uniquement pour l'exécution conteneurisée.

Les dépendances Python sont centralisées dans `requirements.txt` : Django pour le produit, PyYAML pour les configurations, pandas et scikit-learn pour les travaux data, Jupyter pour les laboratoires.

## 2. Installation locale

Depuis un terminal PowerShell :

```powershell
git clone https://github.com/bahdev223/cif-microcredit-scoring.git
cd cif-microcredit-scoring
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell bloque l'activation du virtualenv, utiliser une session autorisée par la politique locale. Éviter d'installer les dépendances globalement.

## 3. Exécuter le produit Django

```powershell
python backend/manage.py migrate
python backend/manage.py check
python backend/manage.py runserver
```

Le premier lancement crée la base SQLite locale et applique les migrations. L'application est accessible tant que le terminal affiche le serveur en cours.

| Adresse | Usage |
| --- | --- |
| `http://127.0.0.1:8000/` | écran de saisie et d'analyse |
| `http://127.0.0.1:8000/api/etat/` | diagnostic rapide du service |
| `http://127.0.0.1:8000/admin/` | administration Django |
| `http://127.0.0.1:8000/api/demandes-credit/analyser/` | API `POST` d'analyse |

Pour arrêter le serveur, utiliser `Ctrl+C` dans son terminal. En cas de réponse HTML à la place du JSON, vérifier le serveur, les migrations et l'URL de la route API.

## 4. Tester l'interface

L'écran d'accueil charge Fatou Traoré, un cas pédagogique. Il contient : identité et demande, activité économique, ménage et engagements, historique, puis un résultat explicable avec score, indicateurs et règles déclenchées.

Un fichier JSON unique peut être importé depuis `donnees/echantillons/`. Respecter le schéma `schema_dossier_saisie.json`. Les CSV synthétiques ne sont pas des dossiers individuels importables directement dans ce formulaire.

## 5. Architecture du dépôt

```text
backend/                         application Django
  api/                           routes d'analyse et état du service
  clients/                       données déclaratives du client
  credits/                       demandes de crédit et scores
  evaluation_risque/             calculs, règles et explications
  audit/                         traçabilité des analyses
  config/                        réglages et routes Django
frontend/                        interface servie par Django
  templates/                     page HTML
  static/                        JavaScript et CSS
donnees/                         données séparées du code
  echantillons/                  JSON pour interface et tests
  synthetiques/brutes/           tables observables générées
  synthetiques/traitees/         résultats et données nettoyées
  synthetiques/variables/        jeux prêts pour les laboratoires
  synthetiques/verite/           paramètres cachés, interdits au modèle
  publiques/                     sources publiques documentées
simulation/                      génération reproductible du monde fictif
  configuration/                 YAML des institutions, secteurs et produits
  generateurs/                   règles de génération par domaine
laboratoires/                    notebooks data science
modeles/                         artefacts entraînés et registre
tests/                           vérifications d'intégrité du monde simulé
documentation/                   guides fonctionnels et techniques
```

`backend/` et `frontend/` constituent le prototype visible. `simulation/` et `donnees/` constituent le laboratoire de données : ils ne sont pas exécutés par le serveur Django lors d'une analyse utilisateur.

## 6. Données synthétiques et simulateur

Le simulateur fabrique cinq institutions de microfinance fictives. Sa graine par défaut est 2026, ce qui rend la génération reproductible à configuration identique.

```powershell
python simulation/generer.py
python tests/verifier_monde.py
```

Pour une expérience distincte :

```powershell
python simulation/generer.py --graine 7
python tests/verifier_monde.py
```

La génération écrit les CSV hors du dépôt dans `C:\Users\hp\cif-microcredit-donnees-locales\synthetiques\` par défaut. Le contrôle doit réussir avant toute utilisation ou publication. Le manifeste sous `verite/manifeste_generation.json` conserve la graine, les tailles et les empreintes des fichiers.

### Règle d'étanchéité

Seules les tables de `brutes/` dans le répertoire local peuvent servir à entraîner ou évaluer un modèle. Le dossier `verite/` est réservé à la validation du simulateur ; il contient des informations impossibles à connaître lors d'une décision réelle. Le lire dans un notebook de scoring créerait une fuite de données.

Le détail de chaque colonne et des contrôles est dans `07-dictionnaire-donnees-synthetiques.md`.

## 7. Laboratoires et modèles

Les notebooks sous `laboratoires/` suivent la progression prévue : exploration, qualité, construction de variables, référence logistique, comparaison, calibration et explicabilité. Ils lisent les données depuis `donnees/` et enregistrent les artefacts validés sous `modeles/`.

Avant de promouvoir un modèle vers le produit, documenter son jeu de données, sa date, sa validation, ses limites et sa version. Aucun modèle entraîné ne doit remplacer les règles de démonstration sans validation métier, juridique et sécurité.

## 8. Docker (optionnel)

Avec Docker Desktop démarré, à la racine du dépôt :

```powershell
docker compose up --build
```

L'application est disponible sur le port `8000`. Pour arrêter les conteneurs :

```powershell
docker compose down
```

La base SQLite et les fichiers du dépôt sont montés dans le conteneur. Ne pas lancer simultanément plusieurs processus qui écrivent dans la même base SQLite.

## 9. Vérifications avant un commit

```powershell
python backend/manage.py check
python tests/verifier_monde.py
git status
```

Si des données synthétiques ont été régénérées, vérifier les contrôles, sans ajouter les CSV au commit. Ne pas versionner `.venv/`, `__pycache__/`, secrets ou données réelles de clients.

## 10. Dépannage rapide

| Symptôme | Vérification |
| --- | --- |
| `python` introuvable | installer Python puis rouvrir le terminal |
| module Django introuvable | activer `.venv` puis exécuter `pip install -r requirements.txt` |
| erreur de table SQLite | exécuter `python backend/manage.py migrate` |
| l'analyse renvoie une page HTML | vérifier l'URL API, le serveur et les migrations |
| fichier JSON refusé | importer un dossier unique conforme au schéma, pas un CSV |
| contrôle du monde en échec | ne pas publier les données ; examiner le premier contrôle en erreur |
