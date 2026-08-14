# Gouvernance du Data Mart Crédit et du futur modèle

## Principe

Le Data Mart Crédit sert à construire et conserver un historique analytique exploitable. Il ne remplace pas le système transactionnel de l'institution. Il relie les données de demande connues à T0 aux performances observées après le crédit.

```text
Données de demande à T0 → analyse / décision humaine → performance observée → évaluation
```

## Temporalité et fuite de données

Pour chaque ancienne demande, le dataset doit être reconstruit avec les seules informations disponibles au jour de cette demande. Un paiement ultérieur, un retard, une clôture ou un défaut est un résultat observé ; il ne peut pas prédire rétroactivement ce même prêt.

Les situations économiques sont donc des snapshots datés, pas une unique situation actuelle attachée au client. Une analyse doit conserver au minimum : date, version du cadre, variables snapshot, calculs, version du modèle éventuel, résultat, recommandation et décision humaine.

## Définition versionnée du résultat

Le « défaut » n'est pas universel. L'institution devra configurer et valider sa définition — par exemple un seuil de jours de retard, des échéances consécutives impayées ou une perte — avec une date d'effet, une fenêtre d'observation et un responsable de validation. La cible est versionnée : changer sa définition change ce que le modèle apprend.

## Qualité et dictionnaire

Le catalogue de données décrit les données de demande et de performance, leur extraction possible, leur couverture et leurs limites. Le contrôle qualité rapporte la complétude, l'actualité, l'unicité, la validité, la cohérence et les éléments impossibles à vérifier automatiquement. Il n'affiche pas de score global sans formule explicite.

## Modes d'accompagnement

| Contexte institution | Mode approprié |
| --- | --- |
| historique suffisant et qualité validée | développement et validation d'un modèle statistique |
| historique insuffisant | cadre métier/règles expertes, collecte rigoureuse et pilote contrôlé |

Les règles expertes ne sont pas un modèle statistique de substitution. Elles peuvent accompagner un pilote jusqu'à ce que les résultats observés permettent une évaluation et un apprentissage responsables.

## Modèle, politique et décision : trois couches distinctes

```text
modèle statistique éventuel
        ↓
estimation / score / PD
        ↓
politique de risque de l'institution
        ↓
orientation : zone favorable / réexamen / zone défavorable
        ↓
agent, responsable ou comité
        ↓
décision humaine tracée
```

Un modèle ne décide jamais seul. Une politique institutionnelle peut prévoir une zone de réexamen manuel entre deux zones de traitement. Ses seuils, conditions, date d'effet, version et valideur relèvent de l'institution : le prototype ne les invente pas.

Le cadre de collecte, le modèle statistique éventuel et la politique de décision sont trois composants indépendants. Modifier l'un ne doit pas modifier silencieusement les autres.

## Validation et monitoring du futur modèle

Un modèle candidat est développé sur des observations historiques, testé hors échantillon et, autant que possible, sur une période ultérieure. Les mesures à documenter incluent au minimum discrimination, calibration, distribution des scores, qualité des données et stabilité temporelle. Les indicateurs possibles — AUC, Gini, KS, matrice de confusion — ne remplacent pas une validation métier.

Le registre de modèles conserve les versions, données et période d'entraînement, définition de la cible, variables, résultats de validation, approbation humaine et date d'effet. Tout changement passe par une validation contrôlée ; aucun réentraînement automatique n'est autorisé.

## Cadres adaptés au contexte

Les cadres de collecte peuvent différer selon l'activité : commerce et agriculture saisonnière ne se décrivent pas avec les mêmes rubriques ni le même rythme de trésorerie. Le schéma canonique conserve les objets communs ; les cadres configurables définissent les informations économiques spécialisées à T0.

Pour l'agriculture saisonnière, une moyenne mensuelle unique peut masquer la capacité réelle de remboursement. Le cadre doit pouvoir documenter campagne, production, charges de campagne et calendrier des flux, puis rendre ces informations exploitables à T0.

## Limites de la démonstration

Les 250 clients fictifs actuels sont adaptés aux tests, au parcours utilisateur et à la démonstration de l'import. Ils ne permettent pas d'affirmer qu'un modèle est robuste. Le passage à un modèle exige des données historiques suffisantes, une cible validée, des contrôles de qualité, une validation et une surveillance continues.

## Architecture de plateforme

La plateforme de scoring est composée de trois couches complémentaires, et non d'un ERP de microfinance :

| Couche | Responsabilités |
| --- | --- |
| Data Platform | ingestion, mapping, qualité, dictionnaire, provenance et Data Mart |
| Analytics Platform | Feature Engine, datasets, définition de cible, Model Lab, validation, registre et monitoring |
| Decision Support | dossier T0, cadre métier, explication, simulation, politique, décision humaine et audit |

## Diagnostic de préparation au scoring

Avant tout développement de modèle, un diagnostic doit dire si une institution est prête à explorer, à entraîner ou seulement à continuer la collecte. Il rapporte notamment : période couverte, volumes de clients et crédits, crédits arrivés à maturité, disponibilité des paiements et retards, couverture des variables T0, qualité par dimension, stabilité des identifiants et définition validée ou non du défaut.

La conclusion doit être descriptive : « prêt pour exploration », « dataset à préparer » ou « données insuffisantes, poursuivre le pilote ». Un pourcentage de maturité éventuel doit être accompagné de sa formule documentée ; il ne peut pas être présenté comme une mesure officielle ou magique.

## Jeux synthétiques

Deux usages doivent rester distincts : un petit jeu pédagogique avec Fatou, Bakary et les autres cas pour l'UX et la démonstration ; un jeu synthétique beaucoup plus volumineux pour éprouver techniquement le Data Mart, les transformations et le laboratoire. Aucun des deux ne constitue une preuve de performance sur une institution réelle.
