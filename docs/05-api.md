# API du prototype

Base locale : `http://127.0.0.1:8000`

## Etat du service

`GET /api/etat/`

Reponse :

```json
{"etat":"operationnel","service":"evaluation-microcredit-cif"}
```

## Analyser une demande de credit

`POST /api/demandes-credit/analyser/`

```json
{
  "nom_complet": "Fatou Traore",
  "secteur_activite": "Commerce",
  "revenu_mensuel": 180000,
  "charges_mensuelles": 65000,
  "anciennete_activite_mois": 36,
  "nombre_retards": 0,
  "regularite_tontine": "reguliere",
  "montant_demande": 300000,
  "duree_mois": 12
}
```

Les valeurs de `regularite_tontine` sont `reguliere`, `partielle` ou `inconnue`. La reponse contient `score_risque`, `niveau_risque`, `recommandation` et `explication`. Chaque appel valide cree aussi un journal d'audit.

Exemple Windows PowerShell :

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/demandes-credit/analyser/ -ContentType 'application/json' -Body '{"nom_complet":"Fatou Traore","secteur_activite":"Commerce","revenu_mensuel":180000,"charges_mensuelles":65000,"anciennete_activite_mois":36,"nombre_retards":0,"regularite_tontine":"reguliere","montant_demande":300000}'
```
