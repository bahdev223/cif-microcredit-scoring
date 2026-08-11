# API du prototype

Base locale : `http://127.0.0.1:8000`

## Etat du service

`GET /api/health/`

Reponse :

```json
{"status":"ok","service":"cif-microcredit-scoring"}
```

## Analyser une demande

`POST /api/credit-applications/analyze/`

```json
{
  "full_name": "Fatou Traore",
  "sector": "Commerce",
  "monthly_income": 180000,
  "monthly_expenses": 65000,
  "business_age_months": 36,
  "late_payments": 0,
  "tontine_regularity": "good",
  "amount": 300000,
  "term_months": 12
}
```

Les valeurs de `tontine_regularity` sont `good`, `medium` ou `none`. La reponse contient le score indicatif, le niveau de risque, la recommandation et les facteurs expliques. Chaque appel valide cree aussi un journal d'audit.

Exemple Windows PowerShell :

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/credit-applications/analyze/ -ContentType 'application/json' -Body '{"full_name":"Fatou Traore","sector":"Commerce","monthly_income":180000,"monthly_expenses":65000,"business_age_months":36,"late_payments":0,"tontine_regularity":"good","amount":300000}'
```
