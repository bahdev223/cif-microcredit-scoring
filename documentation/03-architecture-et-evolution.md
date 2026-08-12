# Architecture et evolution

## V0 Django

```text
backend/               # Django : clients, credits, audit, api et evaluation_risque
frontend/              # templates et fichiers statiques de la demonstration
donnees/              # donnees fictives, publiques et echantillons
simulation/           # monde fictif et futurs generateurs
laboratoires/         # laboratoire Data Science
modeles/              # registre des modeles entraines
```

Le point d'acces `POST /api/demandes-credit/analyser/` persiste un client et une demande, calcule le score et enregistre l'analyse dans l'audit.

## Evolution cible, seulement apres validation

1. Notebook data : explorer un dataset anonymise et comparer regression logistique, arbres et boosting.
2. Service API : isoler le calcul du score derriere une API securisee.
3. Explicabilite : afficher les facteurs d'un modele valide (par exemple SHAP).
4. Audit : tracer la version du modele, les entrees, la recommandation et la decision humaine.
5. Integration : connecter le Core Banking uniquement avec l'accord de l'institution.

Chaque etape doit repondre a un besoin metier observe et ne doit pas etre ajoutee seulement pour faire plus technique.
