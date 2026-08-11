# CIF Microcredit Scoring

Prototype V0 Django d'aide a la decision pour un agent de microfinance. Il analyse un dossier client, estime un niveau de risque et explique clairement les facteurs pris en compte. La decision de credit reste toujours humaine.

## Lancer le prototype

Creer un environnement Python puis installer les dependances :

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Verifier ensuite `GET /api/health/` ou appeler `POST /api/credit-applications/analyze/`.

## Contenu de cette V0

- API de creation et analyse d'une demande de microcredit;
- estimation transparente du risque, basee sur des regles simples;
- explication des facteurs positifs et negatifs;
- persistance des clients, demandes et journaux d'audit SQLite.

## Documentation

- [Vision produit](docs/01-vision-produit.md)
- [Regles et donnees](docs/02-regles-et-donnees.md)
- [Architecture et evolution](docs/03-architecture-et-evolution.md)
- [Guide de demonstration](docs/04-guide-demo.md)
- [Contrat API](docs/05-api.md)

## Limite importante

Cette V0 est une demo de hackathon avec des donnees fictives et des regles pedagogiques. Elle ne doit pas servir a accorder ou refuser un credit reel avant validation metier, juridique, statistique et securitaire.
