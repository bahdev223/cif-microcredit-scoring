# Acquisition externe et dossier consolidé

## Décision de cadrage

La plateforme CIF est une solution d'analyse du risque, pas le système transactionnel de l'institution. Elle ne gère ni encaissement, ni décaissement, ni caisse, ni comptabilité. Elle importe et observe les données produites par le système existant.

## Les deux entrées

### A. Collecte interne : situation actuelle T0

L'agent remplit un formulaire construit selon le cadre défini par l'institution : activité, recettes, charges d'activité, charges du ménage, engagements et documents utiles. Le moteur métier en déduit par exemple une marge disponible ou une pression de remboursement.

### B. Historique importé : données du SI

Les exports CSV ou Excel fournissent l'historique des clients, crédits, échéances, paiements et retards. Une API ou un connecteur n'est envisagé qu'après observation des logiciels et formats réellement utilisés par les institutions.

## Dossier consolidé

```text
Situation actuelle T0 ───┐
                          ├── dossier client consolidé ──► variables à T0 ──► analyse
Historique importé ──────┘
```

Les sources restent identifiables. Une valeur importée ne doit pas écraser une valeur collectée, et les données postérieures à une décision ne doivent jamais devenir des variables utilisées pour cette décision.

## Pipeline d'acquisition à construire

1. dépôt CSV et Excel ;
2. détection des feuilles, colonnes et types ;
3. mapping vers le référentiel CIF ;
4. contrôles de présence, format, relation et cohérence temporelle ;
5. rapport Data Quality et aperçu avant validation ;
6. rapprochement avec les clients ;
7. import de l'historique avec provenance ;
8. alimentation du dossier consolidé et du Feature Engine.

## Schéma commun, cadres spécifiques

Le schéma canonique porte les objets communs à toutes les institutions : client, activité, demande, crédit, échéance et paiement. Les données métier propres à un secteur — recettes, achats, stock pour le commerce ; surface, campagne et charges de campagne pour l'agriculture — sont définies par les cadres configurables de collecte interne.

Les deux convergent dans le dossier à T0 sans confondre les sources ni les usages : l'identification rattache le dossier ; les données analytiques alimentent les calculs ; seules les variables validées peuvent devenir des features candidates.

## Boucle d'évaluation

Après la décision humaine, l'institution continue à gérer le crédit dans son SI. Un export ultérieur fournit le comportement observé : paiements, retards, régularisation ou défaut selon la définition retenue. Ce résultat sert à évaluer le modèle ; tout réentraînement doit être contrôlé, versionné et audité.

## État actuel

Le prototype accepte aujourd'hui un lot CSV structuré et persiste l'historique analytique. La détection automatique de colonnes, le mapping interactif, l'import Excel et le rapprochement avancé restent les prochaines priorités ; ils ne doivent pas être présentés comme déjà livrés.
