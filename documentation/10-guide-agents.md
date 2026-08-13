# Guide de travail pour les agents

Ce document est le contrat de collaboration du dépôt CIF Microcrédit Scoring. Chaque agent reçoit un périmètre limité, travaille sur une branche ou un worktree dédié et remet un résultat vérifié.

## Objectif de la phase actuelle

Construire une fondation fiable : institutions fictives, CSV relationnels, import, qualité, persistance, exploration et interfaces métier.

**Cette phase ne construit aucun modèle de scoring.** Elle ne doit pas introduire de régression logistique, XGBoost, LightGBM, Random Forest, SHAP, probabilité de défaut, seuil automatique d'acceptation ou décision automatique de crédit.

## Règles non négociables

1. Le métier, l'interface et la documentation sont en français.
2. Ne pas modifier les migrations appliquées : créer une migration supplémentaire.
3. Ne pas supprimer ou régénérer les CSV versionnés sans demande explicite.
4. Les fichiers sous `donnees/synthetiques/institution_XX/` sont indépendants et doivent rester importables.
5. Ne jamais utiliser des données cachées pour entraîner un futur modèle.
6. Ne pas inventer de règle métier, de seuil ou d'hypothèse présentée comme une vérité.
7. Ne pas ajouter de dépendance, microservice ou abstraction sans nécessité démontrée.
8. Ne pas écrire de secret, de donnée personnelle réelle, de fichier `.env` ou de base réelle dans Git.
9. Toute modification d'API met à jour `documentation/05-api.md` et `documentation/openapi.yaml`.
10. Toute donnée présentée dans l'interface doit venir de l'API : pas de données métier codées dans JavaScript.
11. Pas de nettoyage annexe hors périmètre.
12. Ne commit/push pas sauf demande explicite.

## Agents et frontières

| Agent | Mission | Périmètre prioritaire |
| --- | --- | --- |
| 01 Architecture | conventions, cohérence globale, plan d'évolution | documentation, structure |
| 02 Simulation | cinq SFD fictives et CSV cohérents | `simulation/`, `donnees/` |
| 03 Import/Qualité | lecture CSV, validation, aperçu, traçabilité | `backend/api/`, tests import |
| 04 Backend métier | API, modèles, persistance, rôles | `backend/` hors scoring |
| 05 Frontend/UX | écrans métier et accessibilité | `frontend/` |
| 06 Data/Statistiques | exploration et préparation descriptive | `laboratoires/`, `documentation/` |
| 07 Scoring/Modèles | **réservé, ne rien construire maintenant** | `modeles/` |
| 08 QA | tests de non-régression et fixtures | `tests/`, `backend/*/tests.py` |
| 09 Documentation | contrats, guides, dictionnaires | `documentation/`, README |

## Données et relations

Chaque institution possède environ 50 clients et ses six fichiers :

- `clients.csv`
- `activites.csv`
- `demandes_credit.csv`
- `credits.csv`
- `echeances.csv`
- `paiements.csv`

Les relations utilisent des identifiants techniques stables. Les données brutes sont immuables : le parcours est **brut → validation → nettoyage → traité → futures variables**.

## Définition de terminé

Avant remise, l'agent indique ses hypothèses, les fichiers modifiés, les tests effectués et les limites éventuelles. Il exécute au minimum :

```powershell
python backend/manage.py check
git diff --check
git status
```

Il exécute aussi les tests liés à son périmètre. Toute modification de `simulation/` ou de données doit exécuter `python tests/verifier_monde.py`.

