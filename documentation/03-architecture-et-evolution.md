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

Le point d'accès `POST /api/demandes-credit/analyser/` persiste une demande, calcule le score et enregistre l'analyse dans l'audit. Il sert à la démonstration du moteur métier ; il n'exécute jamais une décision ou une transaction de crédit.

## Architecture fonctionnelle cible

```text
COLLECTE INTERNE T0                 HISTORIQUE DU SI
formulaire dynamique                CSV / Excel / API plus tard
          │                                  │
          └────────── DOSSIER CONSOLIDÉ ────┘
                           │
              mapping → qualité → variables
                           │
          moteur métier + modèle statistique
                           │
               explication → agent humain
```

Le SI de l'institution reste propriétaire des transactions : il gère le crédit, les échéances et l'encaissement. Notre plateforme reçoit périodiquement les exports nécessaires à l'observation du résultat et à l'évaluation future du modèle.

## Schéma canonique et ingestion

Le schéma canonique est le langage interne partagé par les imports et les moteurs : `client`, `activité`, `demande`, `crédit`, `échéance`, `paiement`, `situation économique` et `produit` si nécessaire. Les colonnes propres à chaque institution sont traduites par un connecteur ou un mapping avant d'entrer dans ce schéma.

```text
CSV / XLSX / API
       │
connecteur ou mapping
       │
schéma canonique → validation → Data Quality → normalisation → persistance
```

L'API d'ingestion est une cible d'évolution. Elle ne doit jamais contourner le mapping, les validations de schéma, les contrôles de relation et le rapport qualité appliqués aux fichiers.

## Evolution cible, seulement apres validation

1. Notebook data : explorer un dataset anonymise et comparer regression logistique, arbres et boosting.
2. Service API : isoler le calcul du score derriere une API securisee.
3. Explicabilite : afficher les facteurs d'un modele valide (par exemple SHAP).
4. Audit : tracer la version du modele, les entrees, la recommandation et la decision humaine.
5. Acquisition : CSV et Excel, détection de colonnes, mapping, aperçu, qualité et rapprochement client.
6. Intégration : connecter le Core Banking uniquement avec l'accord de l'institution, après avoir identifié les formats réellement utilisés.
7. API d'ingestion : exposer des lots ou ressources canoniques, authentifiés et auditables, qui traversent exactement le même pipeline qualité que CSV et Excel.

Chaque etape doit repondre a un besoin metier observe et ne doit pas etre ajoutee seulement pour faire plus technique.
