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

## Data Mart Crédit temporel

Le Data Mart Crédit est la couche analytique construite à partir du schéma canonique. Il sépare strictement :

| Famille | Contenu | Moment |
| --- | --- | --- |
| Données de demande | situation économique, produit, montant, durée, historique déjà connu | T0, avant la décision |
| Données de performance | échéances, paiements, jours de retard, statut, perte éventuelle | après le décaissement |

Chaque ligne analytique doit pouvoir reconstruire ce qui était connu au moment de la demande. Une information produite après T0 ne peut jamais devenir une feature de ce même crédit : c'est une fuite de données.

La cible d'historique pour un futur modèle est idéalement de cinq années, et au minimum trois lorsque cela est possible. Les petites données synthétiques du prototype servent aux tests et à la démonstration ; elles ne prouvent pas la robustesse d'un modèle statistique.

## Evolution cible, seulement apres validation

1. Schéma canonique et dictionnaire de données validés avec les institutions.
2. Acquisition CSV/XLSX, mapping, qualité, aperçu et rapprochement client.
3. Data Mart temporel et snapshots des analyses.
4. Cadres de collecte adaptés aux activités et produits.
5. Feature Engine et laboratoire : exploration, analyse univariée, stabilité temporelle et sélection justifiée des variables.
6. Modèle de référence simple, puis comparaison avec des modèles plus complexes seulement si cela est justifié.
7. Politique de décision versionnée, paramétrée et validée par l'institution.
8. Monitoring, réévaluation et réentraînement contrôlé.
9. API d'ingestion authentifiée et auditée, puis connecteurs SI après identification des formats réels.

Chaque etape doit repondre a un besoin metier observe et ne doit pas etre ajoutee seulement pour faire plus technique.
