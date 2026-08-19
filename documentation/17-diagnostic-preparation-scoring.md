# Diagnostic de préparation au scoring

## Objectif

Avant de promettre un modèle, la plateforme doit pouvoir répondre : « les données de cette institution permettent-elles réellement de commencer un projet de scoring ? » Le diagnostic ne produit ni score de crédit ni décision client.

## Informations contrôlées

| Axe | Questions |
| --- | --- |
| Historique | Quelle période est couverte ? Les anciens enregistrements sont-ils archivés ? |
| Volume | Combien de clients, demandes, crédits et crédits arrivés à maturité ? |
| Performance | Paiements, échéances, retards, statuts et incidents sont-ils disponibles ? |
| T0 | Les données étaient-elles connues à la date de chaque demande ? |
| Couverture | Quel pourcentage est présent pour chaque champ canonique utile ? |
| Qualité | Complétude, actualité, unicité, validité, cohérence et limites d'exactitude |
| Cible | La définition du défaut est-elle validée, datée et versionnée ? |
| Provenance | Les systèmes, lots et règles de mapping sont-ils traçables ? |

## Conclusions autorisées

- **Prêt pour exploration** : historique et qualité permettent d'explorer et de documenter les variables.
- **Dataset à préparer** : les données existent mais demandent mapping, nettoyage, compléments ou définition de cible.
- **Collecte/pilote à poursuivre** : l'historique de performance ou le volume est insuffisant pour un modèle statistique défendable.

Un indicateur synthétique n'est acceptable que si sa formule, ses seuils et ses limites sont documentés. Il ne doit jamais masquer les dimensions qui nécessitent une action.

## Principe d'arrêt

Lorsque le volume, l'historique de performance, la qualité ou la définition de cible sont insuffisants, le diagnostic doit bloquer l'entrée au Model Lab. Il affiche les actions utiles : poursuivre la collecte, corriger les champs prioritaires, compléter les données T0, définir l'outcome ou lancer un pilote contrôlé. Il ne fabrique jamais un score statistique pour combler l'absence de données.

## Démonstration terrain cible

Le parcours le plus utile à montrer à une institution est : déposer un export exemple anonymisé, détecter ses colonnes, mapper son vocabulaire, lire les anomalies et la couverture, puis afficher le diagnostic. Un export vide ou seulement ses en-têtes suffit pour commencer le dictionnaire et préparer le mapping ; aucune base complète ne doit être demandée avant ce travail de découverte.

## Parcours produit cible

```text
Import CSV / XLSX / API
        ↓
Mapping vers le schéma canonique
        ↓
Qualité + couverture + provenance
        ↓
Diagnostic de préparation au scoring
        ↓
Data Mart puis exploration, ou pilote de collecte
```

## Statut

Le premier étage du parcours est disponible : un export CSV/XLSX/XLSM peut être lu sans persistance, sa feuille peut être sélectionnée, ses colonnes peuvent être associées au référentiel canonique puis contrôlées. Le rapport affiche les six dimensions de qualité et les anomalies ligne par ligne. À l'issue de ce contrôle, l'écran affiche un **pré-diagnostic** : il rappelle les sources encore nécessaires et refuse honnêtement de déclarer un modèle prêt depuis un export isolé.

Lorsqu'un lot complet est préparé, le diagnostic agrège les objets reçus et leurs volumes, indique la période lue lorsqu'elle est disponible, les sources manquantes et si la performance est observable grâce aux échéances et paiements. Les données T0 et la cible de défaut restent explicitement **non vérifiées / non définies**. Il peut seulement conclure **Dataset à préparer** ou **Exploration possible** ; il ne rend jamais un modèle « prêt ».

Le diagnostic institutionnel complet reste à approfondir : mesure de période réellement couverte, couverture détaillée des variables T0, provenance persistée ligne par ligne et définition versionnée de la cible avant d'autoriser l'entrée au Model Lab.
