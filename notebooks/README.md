# Laboratoire Data Science

Les notebooks sont exécutés dans l'ordre. Ils utilisent uniquement les fichiers versionnés de `data/` et ne modifient jamais `data/synthetic/raw/`.

| Notebook | Objectif |
| --- | --- |
| `01_exploration.ipynb` | Comprendre les tables et distributions |
| `02_data_quality.ipynb` | Contrôler valeurs manquantes, incohérences et fuite d'information |
| `03_feature_engineering.ipynb` | Construire les variables à la date de demande |
| `04_logistic_baseline.ipynb` | Établir une régression logistique de référence |
| `05_model_comparison.ipynb` | Comparer les modèles avec des métriques adaptées |
| `06_calibration.ipynb` | Vérifier les probabilités prédites |
| `07_explainability.ipynb` | Expliquer les résultats du modèle retenu |

Les notebooks sont initialisés, mais ne contiennent volontairement aucun résultat de modèle avant la génération et validation du dataset synthétique.
