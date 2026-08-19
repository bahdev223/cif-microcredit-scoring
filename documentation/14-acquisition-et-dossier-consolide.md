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

## Pipeline d'acquisition

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

## Connecteurs et mapping

Un connecteur n'est pas un accès direct à la base de l'institution. C'est une configuration traçable qui traduit son vocabulaire vers le schéma canonique CIF.

| Institution source | Schéma canonique CIF |
| --- | --- |
| `customer_number` ou `num_societaire` | `client_id_source` |
| `turnover` ou `ca_mensuel` | `recettes_activite` |
| `loan_amount` ou `montant_pret` | `montant_credit` |
| `payment_date` ou `date_reglement` | `date_paiement` |

Le connecteur doit conserver sa version, les règles de transformation, les colonnes absentes, les rejets et la provenance du lot. Il alimente ensuite le pipeline commun : normalisation, validation, Data Quality, aperçu et persistance.

## Boucle d'évaluation

Après la décision humaine, l'institution continue à gérer le crédit dans son SI. Un export ultérieur fournit le comportement observé : paiements, retards, régularisation ou défaut selon la définition retenue. Ce résultat sert à évaluer le modèle ; tout réentraînement doit être contrôlé, versionné et audité.

## Qualité des données par dimension

Le rapport de qualité ne doit pas se limiter à un pourcentage global opaque. Il doit exposer séparément :

| Dimension | Question contrôlée |
| --- | --- |
| Complétude | les champs nécessaires sont-ils renseignés ? |
| Actualité | les données sont-elles assez récentes pour l'usage ? |
| Unicité | les identifiants et lignes censées être uniques le sont-ils ? |
| Validité | le format, le type et le domaine sont-ils acceptables ? |
| Cohérence | les relations et les dates sont-elles compatibles ? |
| Exactitude | la valeur correspond-elle à la réalité ? — non vérifiable automatiquement dans la plupart des cas |

Un rapport distingue les erreurs bloquantes, les avertissements et ce qui ne peut pas être vérifié automatiquement.

## État actuel du prototype

L'écran **Importer des données** accepte maintenant un export CSV, XLSX ou XLSM pour une analyse préparatoire. Il lit la feuille choisie, expose un aperçu, propose une table canonique et des associations de colonnes, puis contrôle le mapping corrigé par l'utilisateur selon les six dimensions de qualité.

Cette étape n'écrit volontairement rien dans la base : `Analyser` et `Contrôler cette correspondance` servent à comprendre l'export et à préparer un connecteur versionné. Lorsque plusieurs exports mappés sont ajoutés au **lot de préparation**, le système contrôle leurs relations (client → demande → crédit → échéance/paiement), produit un diagnostic de couverture puis autorise l'import. Une fois importés, les clients et leurs historiques sont accessibles dans le parcours **Clients → Dossier client**.

Le rapprochement avancé entre sources hétérogènes et la provenance ligne par ligne restent à livrer. Le parcours CSV normalisé de démonstration reste disponible séparément.

## Entrée universelle et provenance

CSV/Excel constitue l'intégration manuelle ; l'API constituera l'intégration automatisée. Les trois sources doivent utiliser le même pipeline, avec le même schéma canonique et les mêmes contrôles.

Pour chaque donnée importante, le Data Mart doit pouvoir conserver, lorsque disponible : valeur, système source, fichier ou lot, mode de collecte, date d'observation, date d'import, niveau de vérification et version du connecteur. La question « d'où vient cette information ? » doit pouvoir être résolue sans interprétation manuelle.
