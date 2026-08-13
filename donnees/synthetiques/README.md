# Données synthétiques locales

Les CSV de simulation ne sont pas versionnés dans Git : ils sont volumineux et sont régénérables.

Par défaut, les données locales sont stockées hors du dépôt dans :

```text
C:\Users\hp\cif-microcredit-donnees-locales\synthetiques\
```

Pour choisir un autre emplacement, définir la variable PowerShell avant de lancer un script :

```powershell
$env:CIF_REPERTOIRE_DONNEES = 'D:\mes-donnees-cif\synthetiques'
python simulation/generer.py
```

Lancer ensuite `python tests/verifier_monde.py`. Les petits exemples importables dans l'interface restent dans `donnees/echantillons/` et sont bien inclus dans Git.
