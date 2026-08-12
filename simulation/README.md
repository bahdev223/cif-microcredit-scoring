# Simulation - monde fictif

Ce dossier contiendra le générateur reproductible de la SFD fictive. Il ne fait pas partie du produit Django et ses règles internes ne doivent pas être utilisées directement par le futur modèle de scoring.

Les fichiers de `configuration/` décrivent l'institution, les produits, secteurs et horizon de simulation. Les générateurs créeront ensuite les tables CSV de `donnees/synthetiques/brutes/`.

## Générer explicitement les données

```powershell
python simulation/generer.py
```

La génération réécrit les neuf fichiers CSV de `donnees/synthetiques/brutes/`. Elle est déterministe : même graine et même configuration donnent exactement les mêmes tables. Les paramètres sont dans `configuration/simulation.yaml`.
