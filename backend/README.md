# Backend Django

Le backend sert la page de démonstration, expose l'API d'analyse et enregistre les dossiers et journaux d'audit dans SQLite.

## Lancer localement

Depuis la racine du dépôt :

```powershell
python backend/manage.py migrate
python backend/manage.py runserver
```

Le serveur écoute sur `http://127.0.0.1:8000/`. Vérifier la configuration avant le lancement :

```powershell
python backend/manage.py check
```

## Modules métier

| Dossier | Rôle |
| --- | --- |
| `api/` | routes HTTP et validation des demandes reçues |
| `clients/` | modèle du client et ses informations déclaratives |
| `credits/` | demande de crédit et résultat de l'analyse |
| `evaluation_risque/` | caractéristiques, règles, prédiction et explication |
| `audit/` | journal des analyses effectuées |
| `config/` | paramètres Django et routes principales |

Les routes sont documentées dans [le contrat API](../documentation/05-api.md). La base SQLite locale est séparée des CSV du simulateur.

