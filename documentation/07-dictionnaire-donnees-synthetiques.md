# Dictionnaire du monde synthétique

Ce document est le contrat du simulateur. Il décrit le monde fictif table par table et colonne par colonne : type, domaine de valeurs, loi de génération, dépendances, évolution dans le temps, visibilité par le modèle et justification métier.

Il est normatif. `simulation/generer.py` et les tests de `tests/` doivent s'y conformer ; toute divergence est un bug du générateur, ou une évolution à écrire ici d'abord.

Rien de ce qui suit ne décrit une institution réelle, ni ne prétend reproduire des statistiques du secteur de la microfinance malienne. Ce sont des paramètres de laboratoire, choisis pour produire des contrastes exploitables.

---

## 1. Principe fondateur : deux mondes séparés

Le simulateur connaît la « personnalité financière » de chaque client. Le modèle de scoring ne doit jamais la voir : il doit la redécouvrir indirectement à travers un historique observable, comme le ferait un agent de crédit.

```text
        MONDE CACHÉ (verite/)                    MONDE OBSERVABLE (brutes/)
        connu du seul simulateur                 ce que l'institution a enregistré
   ┌─────────────────────────────┐          ┌──────────────────────────────────┐
   │ discipline_paiement  0.82   │          │ 3 crédits antérieurs             │
   │ vulnerabilite_choc   0.35   │   ═══>   │ 2 retards de moins de 5 jours    │
   │ volatilite_revenus   0.24   │  produit │ CA déclaré 310 000 F en 2023-04  │
   │ recettes réelles de 60 mois │          │ demande de 500 000 F sur 12 mois │
   │ défaut contrefactuel = oui  │          │ (le reste est inconnu)           │
   └─────────────────────────────┘          └──────────────────────────────────┘
                  🚫 jamais fourni au modèle              ✅ seule source d'entraînement
```

Quatre règles en découlent :

1. **Aucun paramètre latent dans `brutes/`.** Un nom de colonne comme `profil_synthetique`, `risque_latent`, `saisonnalite` ou `scenario` y est interdit.
2. **Aucune trajectoire complète dans `brutes/`.** Une SFD n'observe pas les recettes mensuelles de 50 000 clients pendant 60 mois : elle enregistre ce qu'un agent a noté à quelques dates. La série mensuelle réelle est le moteur du monde, elle vit dans `verite/`.
3. **Aucune colonne calculable dans `brutes/`.** `jours_retard` se déduit de `date_paiement − date_exigible` ; il appartient à `traitees/`. Les données brutes enregistrent des faits, pas des indicateurs.
4. **Aucune information postérieure à la date de décision dans une variable de scoring.** Vérifié par test, pas par bonne volonté.

---

## 2. Ordre de génération

L'ordre est capital : on ne crée pas 50 000 clients avant d'avoir construit le monde économique dans lequel ils vont vivre. Chaque couche ne dépend que des précédentes.

```text
COUCHE 0 — LE DÉCOR                        COUCHE 2 — LE CYCLE DE CRÉDIT
  01 institutions                            09 demandes de crédit
  02 agences                                 10 décisions
  03 agents de crédit                        11 crédits
  04 produits de crédit                      12 échéances
  05 secteurs d'activité                     13 paiements
COUCHE 1 — LA POPULATION                   COUCHE 3 — CE QUI EN RÉSULTE
  06 clients                                 14 résultats observés
  07 activités                             COUCHE 4 — LA DÉGRADATION
  08 situations mensuelles                   injection tracée d'anomalies
```

Le numéro d'une table est son rang de génération. Il figure dans son nom de fichier, dans les deux dossiers : `01_institutions.csv` est observable, `08_situations_mensuelles.csv` ne l'est pas. Le numéro dit l'ordre, le dossier dit la visibilité.

État d'avancement : **les quatorze couches sont implémentées**, ainsi que la dégradation volontaire. Le monde a été généré et contrôlé sur `INS-001` avec 100 clients ; les quatre autres institutions n'attendent que le passage à l'échelle.

Deux réserves à lever avant de considérer le monde comme abouti : les **cas dorés** (`personnages.yaml`) ne sont pas encore écrits, et les **intérêts sont nuls** tant qu'aucun taux défendable n'est arrêté (§6.6).

---

## 3. Cinq institutions, cinq mondes

Le laboratoire ne simule pas une SFD mais cinq, aux portefeuilles volontairement contrastés. C'est ce qui permet de poser la question qui nous intéresse : **un même moteur de scoring s'adapte-t-il à des environnements différents, ou n'apprend-il que le monde qui l'a vu naître ?**

| Identifiant | Profil | Zone | Spécialisation | Ce qu'il permet de tester |
| --- | --- | --- | --- | --- |
| `INS-001` | `URBAIN_COMMERCE` | urbaine | commerce | cycles courts, peu de saisonnalité, données propres |
| `INS-002` | `RURAL_AGRICOLE` | rurale | agriculture | saisonnalité forte, chocs sectoriels, données sales |
| `INS-003` | `ENTREPRENEURIAL_TPE` | mixte | artisanat et TPE | durées longues, montants élevés, octroi exigeant |
| `INS-004` | `GENERALISTE` | mixte | diversifié | référence de calibration |
| `INS-005` | `PORTEFEUILLE_COMPLEXE` | mixte | diversifié | croissance agressive, octroi laxiste, clientèle fragile |

Un modèle entraîné sur `INS-001` et appliqué à `INS-002` doit se dégrader. Un modèle entraîné sur `INS-005` doit avoir appris un tout autre risque de base. Ces écarts sont le résultat attendu, pas un défaut du monde.

Les paramètres qui produisent ces différences sont dans `simulation/configuration/institutions.yaml` : composition sectorielle, orientation produit, sévérité d'octroi, taux de défaut visé, qualité du système d'information, croissance du portefeuille. **Aucun n'est publié dans `brutes/`.**

---

## 4. Horizon et volumétrie

| Paramètre | Valeur de référence | Remarque |
| --- | --- | --- |
| Début du monde | `2021-01-01` | aucun événement généré avant |
| Fin du monde | `2025-12-31` | aucun événement généré après, paiements compris |
| Pas économique | mensuel | situation de chaque client, chaque mois |
| Pas transactionnel | journalier | décaissements, échéances, paiements |
| Clients | 10 000 par institution, soit 50 000 | paramétrable : 200 par institution pour les tests |
| Agences | 41 au total, de 6 à 11 par institution | — |
| Agents de crédit | déduit de `clients_par_agent_cible` | environ 160 au total |
| Produits | 5, offerts avec des poids différents selon l'institution | — |
| Secteurs | 8 | — |
| Graine | 2026 | inscrite dans le manifeste de génération |

### Arrivée progressive des clients

Tous les clients n'existent pas au premier jour. Chaque institution démarre avec un stock de clients déjà en relation, puis en recrute selon sa croissance propre :

```text
nouveaux_clients(année) ∝ (1 + croissance_annuelle_portefeuille) ^ (année − 2021)
normalisé pour que le total atteigne nombre_clients_cible − stock_initial
```

Les clients du stock initial ont une `date_entree_relation` antérieure à 2021 : leur historique de crédit avant cette date n'existe dans aucune table. Cette **censure à gauche** est volontaire — une base réelle commence toujours à une date d'informatisation.

Les paramètres du §3 produisent des populations très différentes : `INS-001` démarre avec 22 % de son portefeuille et croît de 12 % l'an, tandis que `INS-005` démarre avec 6 % et croît de 28 %. Les clients de la seconde ont donc, en moyenne, des historiques bien plus courts — ce qui est exactement la difficulté qu'un scoring rencontre dans une institution jeune.

Sortie de relation : risque mensuel de 0,5 %, triplé dans les six mois qui suivent un défaut.

### Volumétrie attendue

Ordres de grandeur pour les cinq institutions réunies, à confronter aux chiffres réels après la première génération complète :

| Table | Lignes attendues | Poids indicatif |
| --- | --- | --- |
| `06_clients` | 50 000 | 6 Mo |
| `07_activites` | 120 000 – 150 000 | 16 Mo |
| `08_situations_mensuelles` (vérité) | 2 200 000 – 2 600 000 | 180 Mo |
| `09_demandes_credit` | 105 000 – 130 000 | 15 Mo |
| `10_decisions_credit` | 105 000 – 130 000 | 11 Mo |
| `11_credits` | 75 000 – 90 000 | 10 Mo |
| `12_echeances` | 700 000 – 900 000 | 60 Mo |
| `13_paiements` | 800 000 – 1 050 000 | 70 Mo |

Ces volumes restent modestes pour un traitement par lots, mais plus pour un `pandas.read_csv` naïf répété à chaque cellule de cahier. **Décisions à acter avant la couche 08** : les tables de plus de 5 Mo sont écrites en Parquet en plus du CSV, elles sont partitionnées par institution, et le dépôt Git ne versionne que la configuration, le manifeste et un échantillon reproductible (`--echantillon`), le monde complet se régénérant à l'identique depuis la graine.

---

## 5. Conventions communes

| Sujet | Règle |
| --- | --- |
| Format | CSV, séparateur `,`, encodage UTF-8, fin de ligne `\n`, en-tête obligatoire |
| Noms de colonnes | français, `snake_case`, sans accent, stables dans le temps |
| Nom de fichier | `NN_nom_de_table.csv`, `NN` étant le rang de génération |
| Dates | ISO `AAAA-MM-JJ`. Les mois s'écrivent `AAAA-MM` |
| Montants | entiers, en francs CFA (XOF), sans décimale ni séparateur de milliers |
| Taux, ratios, coefficients | décimal à 4 chiffres, point décimal, jamais de pourcentage textuel |
| Booléens | `0` / `1` |
| Valeur manquante | champ vide. Jamais `NA`, `NULL`, `None`, `-1` |
| Identifiants | préfixe et numéro à largeur fixe : `INS-001`, `AGE-001`, `AGT-0001`, `PRO-001`, `SEC-01`, `CLT-000001`, `ACT-000001`, `DEM-000001`, `DEC-000001`, `CRD-000001`, `ECH-0000001`, `PAI-0000001`, `EVT-000001` |
| Clé de partition | `identifiant_institution` figure dans **toutes** les tables. Ces données sont l'agrégation de cinq systèmes d'information distincts, pas une base unique normalisée : la clé n'est donc pas un champ dérivé mais l'identité de la source |
| Tri | chaque fichier est trié par sa clé primaire, pour que deux générations identiques donnent deux fichiers identiques octet pour octet |
| Aléa | un flux aléatoire par entité, dérivé de la graine globale (`graine_client = graine ⊕ hash(identifiant_client)`). Aucune dépendance à l'ordre d'exécution, donc parallélisable sans casser la reproductibilité |

### Ce que le monde ne contient pas

Aucun attribut sensible dans les tables observables : ni sexe, ni âge, ni situation matrimoniale, ni appartenance ethnique ou religieuse, ni nombre d'enfants, ni état de santé. Les agents portent un nom fictif ; les clients n'ont pas de nom du tout, seulement un identifiant.

C'est un choix de conception : ces variables ne sont pas nécessaires pour démontrer le pipeline, et leur présence dans un jeu d'entraînement crée un risque de discrimination directe ou indirecte. Un futur laboratoire d'équité pourra générer un attribut protégé **dans `verite/` uniquement**, pour mesurer un biais sans jamais l'apprendre.

---

## 6. Couche 0 — le décor

### 6.1 `brutes/01_institutions.csv`

Grain : une ligne par institution. Cinq lignes. Entièrement déterministe : rien n'est tiré au hasard, tout vient de `configuration/institutions.yaml`.

| Colonne | Type | Domaine | Génération et dépendances | Rôle métier |
| --- | --- | --- | --- | --- |
| `identifiant_institution` | texte | `INS-001` à `INS-005` | rang dans le fichier de configuration | clé primaire, clé de partition de tout le monde |
| `libelle_institution` | texte | libellé neutre | configuration | lisibilité ; les noms commerciaux fictifs peuvent attendre |
| `code_profil_portefeuille` | catégorie | `URBAIN_COMMERCE`, `RURAL_AGRICOLE`, `ENTREPRENEURIAL_TPE`, `GENERALISTE`, `PORTEFEUILLE_COMPLEXE` | configuration | désigne l'environnement, information légitime pour un modèle multi-institutions |
| `zone_dominante` | catégorie | `urbaine`, `semi_urbaine`, `rurale`, `mixte` | configuration | conditionne le mix sectoriel des agences |
| `specialisation_principale` | catégorie | code secteur ou `DIVERSIFIE` | configuration ; **doit correspondre au secteur dominant du mix latent**, contrôlé à la génération | cohérence entre ce que l'institution déclare et ce que son portefeuille est |
| `date_agrement` | date | 2003-11-02 à 2018-09-12 | configuration | ancienneté de l'institution |
| `pays_de_demonstration` | texte | `Mali` | configuration | contexte de démonstration, fictif |
| `est_fictive` | booléen | toujours `1` | constante | toute extraction de ces données se signale elle-même comme synthétique |

Le taux de défaut visé, la sévérité d'octroi, la composition sectorielle et la qualité du système d'information **ne sont pas dans cette table**. Ils sont latents.

### 6.2 `verite/01_profils_institutions.csv`

Grain : une ligne par institution. Les paramètres qui font qu'un portefeuille se comporte autrement qu'un autre.

| Colonne | Type | Domaine | Effet dans le monde |
| --- | --- | --- | --- |
| `nombre_clients_cible` | entier | 10 000 | taille de la population à générer |
| `nombre_agences` | entier | 6 à 11 | maillage |
| `clients_par_agent_cible` | entier | 240 à 380 | détermine l'effectif d'agents ; un portefeuille chargé s'instruit moins finement |
| `part_clients_stock_initial` | décimal | 0,06 à 0,22 | part des clients déjà présents au 2021-01-01, donc longueur des historiques |
| `croissance_annuelle_portefeuille` | décimal | 0,07 à 0,28 | rythme de recrutement |
| `severite_octroi` | décimal | 0,35 à 0,70 | décale le seuil d'acceptation de la règle de décision |
| `taux_acceptation_cible` | décimal | 0,64 à 0,86 | cible de calibration de la couche 10 |
| `taux_defaut_experimental_cible` | décimal | 0,07 à 0,18 | cible de calibration de la couche 14 |
| `multiplicateur_montant` | décimal | 0,85 à 1,30 | échelle des montants octroyés |
| `decalage_discipline` | décimal | −0,12 à +0,05 | décale la moyenne de `discipline_paiement` du portefeuille |
| `decalage_volatilite` | décimal | −0,02 à +0,10 | décale la volatilité des revenus |
| `sensibilite_macro` | décimal | 0,80 à 1,40 | amplifie ou atténue les chocs sectoriels |
| `facteur_qualite_donnees` | décimal | 0,70 à 1,80 | multiplie les taux d'anomalies injectées (§11) |
| `rotation_annuelle_agents` | décimal | 0,06 à 0,16 | départs d'agents, donc ruptures de pratique d'octroi |

### 6.3 `verite/01_mix_sectoriel.csv` et `verite/01_mix_produits.csv`

Format long : une ligne par institution et par code.

| Fichier | Colonnes | Contrainte |
| --- | --- | --- |
| `01_mix_sectoriel.csv` | `identifiant_institution`, `code_secteur`, `poids_population` | somme des poids = 1,0000 par institution |
| `01_mix_produits.csv` | `identifiant_institution`, `code_produit`, `poids_octroi` | somme des poids = 1,0000 par institution |

Ces poids sont des **cibles de génération**, pas des observations. Ce que le modèle verra, c'est la composition réellement obtenue en comptant les clients par secteur — laquelle s'écartera légèrement de la cible, comme dans la vraie vie.

Le format long évite une table large et creuse, et permet d'ajouter un secteur sans changer le schéma.

### 6.4 `brutes/02_agences.csv`

En mode échantillon, le décor est mis à l'échelle du nombre de clients demandé : générer huit agences pour cent clients n'aurait aucun sens. Le minimum reste de deux agences et trois agents, pour préserver l'hétérogénéité qui fait l'intérêt du monde.

| Colonne | Type | Domaine | Génération et dépendances | Rôle métier |
| --- | --- | --- | --- | --- |
| `identifiant_agence` | texte | `AGE-001`… | numérotation continue sur les cinq institutions | clé primaire |
| `identifiant_institution` | texte | clé étrangère | `nombre_agences` du profil latent | rattachement |
| `libelle_agence` | texte | libellé fictif | — | lisibilité |
| `zone` | catégorie | `urbaine`, `semi_urbaine`, `rurale` | tirée autour de la `zone_dominante` de l'institution : une institution rurale garde 1 ou 2 agences urbaines | l'hétérogénéité interne à une institution est aussi un objet d'étude |
| `date_ouverture` | date | 2003 à 2025 | ≥ `date_agrement` ; 15 % des agences ouvrent pendant la simulation | une agence jeune a un portefeuille jeune : à ne pas confondre avec une clientèle risquée |
| `date_fermeture` | date ou vide | ≤ fin du monde | rare, 2 % | discontinuité de portefeuille |

### 6.5 `brutes/03_agents_credit.csv`

| Colonne | Type | Domaine | Génération et dépendances | Rôle métier |
| --- | --- | --- | --- | --- |
| `identifiant_agent` | texte | `AGT-0001`… | effectif = `nombre_clients_cible / clients_par_agent_cible` | clé primaire |
| `identifiant_institution` | texte | clé étrangère | — | partition |
| `identifiant_agence` | texte | clé étrangère | répartition équilibrée | rattachement |
| `nom_agent` | texte | prénom et nom fictifs | tirage dans une liste fictive documentée | lisibilité ; aucun nom réel |
| `date_entree_fonction` | date | ≥ ouverture de l'agence | uniforme | ancienneté |
| `date_sortie_fonction` | date ou vide | ≤ fin du monde | risque annuel = `rotation_annuelle_agents` | un portefeuille qui change de main change de pratique |

La **sévérité** propre à chaque agent est latente : `verite/03_profils_agents.csv`.

### 6.6 `brutes/04_produits_credit.csv`

Cinq produits, référentiel commun aux cinq institutions, mais offerts avec des poids différents (`01_mix_produits`).

| Colonne | Type | Domaine | Rôle |
| --- | --- | --- | --- |
| `identifiant_produit` | texte | `PRO-001` à `PRO-005` | clé primaire |
| `code_produit` | catégorie | `CREDIT_COMMERCE`, `CREDIT_EQUIPEMENT`, `CREDIT_AGRICOLE`, `FONDS_ROULEMENT`, `MICROCREDIT_GENERAL` | code stable, référencé par les mix produits |
| `libelle_produit` | texte | libellé métier | affichage |
| `montant_min`, `montant_max` | entier FCFA | voir tableau | bornes d'octroi |
| `duree_min_mois`, `duree_max_mois` | entier | 3 à 24 | bornes de durée |
| `periodicite` | catégorie | `mensuelle`, `trimestrielle`, `in_fine` | rythme des échéances |
| `type_amortissement` | catégorie | `mensuel_constant`, `differe_puis_mensuel`, `in_fine` | forme de l'échéancier |
| `differe_max_mois` | entier | 0 à 6 | délai avant la première échéance |
| `secteurs_cibles` | texte | codes secteurs séparés par `|` | conditionne l'éligibilité |
| `date_lancement` | date | ≤ 2021-01-01 sauf un produit lancé en cours de route | crée une rupture temporelle exploitable pour les tests de dérive |

| Code | Montant indicatif | Durée | Amortissement | Secteurs visés |
| --- | --- | --- | --- | --- |
| `MICROCREDIT_GENERAL` | 25 000 – 250 000 | 3 – 9 mois | mensuel constant | tous |
| `FONDS_ROULEMENT` | 50 000 – 600 000 | 3 – 12 mois | mensuel constant | commerce, restauration, transport, services |
| `CREDIT_COMMERCE` | 100 000 – 900 000 | 6 – 12 mois | mensuel constant | commerce |
| `CREDIT_AGRICOLE` | 100 000 – 800 000 | 6 – 12 mois | différé 4 à 6 mois puis mensuel | agriculture, élevage |
| `CREDIT_EQUIPEMENT` | 150 000 – 1 500 000 | 12 – 24 mois | mensuel constant | artisanat, petite production, transport, services |

**Le taux d'intérêt n'est volontairement pas fixé à ce stade.** Inventer une tarification sans base métier reviendrait à publier une politique de prix qui n'engage personne et que personne n'a validée. Le champ `taux_interet_mensuel` sera ajouté quand un paramètre défendable sera disponible, avec sa source ; d'ici là, les échéanciers seront produits à taux nul et documentés comme tels, ou le paramètre sera pris comme hypothèse explicite du scénario.

### 6.7 `brutes/05_secteurs_activite.csv`

| Colonne | Type | Domaine | Rôle |
| --- | --- | --- | --- |
| `identifiant_secteur` | texte | `SEC-01` à `SEC-08` | clé primaire |
| `code_secteur` | catégorie | voir liste | référencé par les mix et par les clients |
| `libelle_secteur` | texte | libellé | affichage |
| `cycle_activite` | catégorie | `continu`, `saisonnier`, `tres_saisonnier` | qualifie le rythme économique |

Codes : `COMMERCE`, `AGRICULTURE`, `ELEVAGE`, `ARTISANAT`, `RESTAURATION`, `TRANSPORT`, `SERVICES`, `PETITE_PRODUCTION`.

Cette nomenclature est **une nomenclature de laboratoire**. Ce n'est ni la NAEMA, ni une classification officielle. Si le projet doit un jour dialoguer avec des données réelles, il faudra la remplacer par une nomenclature sourcée et documenter la table de correspondance.

Les paramètres économiques de chaque secteur — marge structurelle, amplitude saisonnière, mois de pic, volatilité de base — sont latents : `verite/05_parametres_secteurs.csv`.

---

## 7. Couche 1 — la population

### 7.1 `brutes/06_clients.csv`

Grain : un client. **Aucun historique dans cette table** : ce qui évolue vit dans les activités et les crédits.

| Colonne | Type | Domaine | Génération et dépendances | Rôle métier |
| --- | --- | --- | --- | --- |
| `identifiant_client` | texte | `CLT-000001` à `CLT-050000` | `CLT-000001` à `CLT-000200` réservés aux cas dorés, 40 par institution | clé primaire |
| `identifiant_institution` | texte | clé étrangère | — | partition |
| `identifiant_agence` | texte | clé étrangère | agence ouverte à la date d'entrée | rattachement |
| `date_entree_relation` | date | 2014 à 2025-12-31 | calendrier d'arrivée du §4 | ancienneté de relation, variable de scoring majeure |
| `date_sortie_relation` | date ou vide | ≥ entrée | risque mensuel 0,5 %, triplé après défaut | attrition |
| `code_secteur_principal` | catégorie | clé étrangère | tirage selon `01_mix_sectoriel` de l'institution, ajusté par la zone de l'agence | déterminant de la saisonnalité et de la marge |
| `anciennete_activite_mois_a_entree` | entier | 0 à 360 | log-normale, médiane 48 mois | une activité de 15 ans ne se comporte pas comme une activité de 6 mois |
| `possede_compte_epargne` | booléen | 0/1 | 60 % de oui, corrélé à la discipline latente | signal comportemental classique en microfinance |
| `montant_epargne_a_entree` | entier FCFA ou vide | 0 à 2 000 000 | vide si pas de compte, sinon log-normale de médiane 45 000 | capacité d'absorption d'un choc |

### 7.2 `brutes/07_activites.csv`

Grain : **une activité économique**, pas un client et pas un mois. Un client peut en exercer plusieurs — un commerçant qui fait aussi du transport.

| Colonne | Type | Domaine | Génération et dépendances | Rôle métier |
| --- | --- | --- | --- | --- |
| `identifiant_activite` | texte | `ACT-000001`… | 1,3 activité par client en moyenne | clé primaire |
| `identifiant_client` | texte | clé étrangère | — | rattachement |
| `identifiant_institution` | texte | clé étrangère | — | partition |
| `code_secteur` | catégorie | clé étrangère | secteur principal pour la première activité | — |
| `libelle_activite` | texte | libellé court fictif | tirage par secteur | réalisme des démonstrations |
| `est_activite_principale` | booléen | 0/1 | une seule principale par client | pondération des revenus |
| `date_debut_activite` | date | — | déduite de `anciennete_activite_mois_a_entree` | ancienneté de l'activité, distincte de l'ancienneté de relation |
| `date_fin_activite` | date ou vide | — | 8 % des activités secondaires s'arrêtent | une activité qui cesse est un signal |

Les paramètres économiques de l'activité — niveau de recettes, marge, volatilité, saisonnalité, croissance — sont **latents** : `verite/07_parametres_activites.csv`. Ce que l'institution observe d'une activité, ce sont les relevés datés de la table 07 bis.

### 7.3 `brutes/07b_releves_activite.csv`

C'est le point le plus important du dictionnaire.

Une SFD n'observe pas la trajectoire économique de ses clients. Elle enregistre ce qu'un agent a noté, à des dates précises : à l'entrée en relation, lors de l'instruction d'une demande, lors d'une visite de suivi. Le reste du temps, elle ne sait rien.

La vraie série mensuelle existe — dans `verite/08_situations_mensuelles.csv`. La table observable n'en est qu'un **échantillon épars, daté et déclaratif**.

| Colonne | Type | Domaine | Génération et dépendances | Rôle métier |
| --- | --- | --- | --- | --- |
| `identifiant_releve` | texte | `REL-000001`… | 2 à 4 relevés par client | clé primaire |
| `identifiant_activite` | texte | clé étrangère | — | rattachement |
| `identifiant_institution` | texte | clé étrangère | — | partition |
| `date_releve` | date | dans la fenêtre de relation | 1 à l'entrée, 1 par instruction de demande, environ 1 visite par an pour les clients à crédit actif | fixe la date d'observation, donc la limite anti-fuite |
| `origine_releve` | catégorie | `entree_relation`, `instruction_demande`, `visite_suivi` | déterminée par l'événement déclencheur | un chiffre déclaré pour obtenir un crédit n'a pas la fiabilité d'un chiffre relevé en visite |
| `recettes_mensuelles_declarees` | entier FCFA ou vide | 0 à 5 000 000 | valeur réelle du mois, **majorée de 0 à 25 %** si `origine_releve = instruction_demande` | le client se présente sous son meilleur jour ; ce biais existe et le modèle doit vivre avec |
| `charges_mensuelles_declarees` | entier FCFA ou vide | 0 à 5 000 000 | valeur réelle, minorée de 0 à 20 % en instruction | idem, en sens inverse |
| `stock_estime` | entier FCFA ou vide | 0 à 8 000 000 | proportionnel aux recettes pour le commerce, souvent vide pour les services | actif mobilisable |
| `autres_revenus_menage` | entier FCFA ou vide | 0 à 800 000 | log-normale, vide dans 35 % des cas | capacité de remboursement hors activité |
| `charges_menage` | entier FCFA ou vide | 0 à 1 200 000 | proportionnel au revenu du ménage | reste à vivre |
| `dette_externe_mensualite` | entier FCFA ou vide | 0 à 600 000 | non nul pour 22 % des relevés, croissant dans le scénario d'endettement | endettement hors institution, angle mort classique du scoring |

### 7.4 `verite/08_situations_mensuelles.csv`

Grain : une activité × un mois de vie. Environ 2,4 millions de lignes. **C'est le moteur du monde, et il n'est jamais publié en observable.**

| Colonne | Type | Domaine | Calcul |
| --- | --- | --- | --- |
| `identifiant_activite` | texte | clé étrangère | — |
| `identifiant_institution` | texte | clé étrangère | partition |
| `mois` | mois | `AAAA-MM` | — |
| `recettes_reelles` | entier FCFA | > 0 | voir formule |
| `charges_reelles` | entier FCFA | ≥ 0 | recettes × (1 − marge) × indice de charges macro |
| `revenu_net_reel` | entier FCFA | peut être négatif | recettes − charges |
| `tresorerie_disponible` | entier FCFA | peut être négatif | trésorerie du mois précédent + revenu net − charges du ménage − échéances payées |
| `indice_saison` | décimal | 0,40 à 1,80 | composante saisonnière du mois |
| `effet_evenement` | décimal | 0,20 à 2,00 | produit des événements actifs |
| `effet_macro` | décimal | 0,70 à 1,30 | contexte du secteur, amplifié par `sensibilite_macro` de l'institution |

```text
recettes(t) = niveau_initial
              × (1 + croissance_annuelle)^(t/12)      tendance de fond
              × saison(mois, amplitude, mois_pic)      cycle annuel
              × macro(secteur, t) ^ sensibilite_macro  contexte, propre à l'institution
              × effet_evenement(t)                     chocs individuels
              × exp(ε_t − σ²/2),  ε_t = ρ·ε_{t−1} + bruit,  ρ = 0,5
```

L'autocorrélation `ρ = 0,5` est essentielle : sans elle, un mauvais mois n'aurait aucune conséquence sur le suivant et les difficultés ne s'enchaîneraient jamais de façon réaliste.

---

## 8. Couche 2 — le cycle de crédit

### 8.1 `brutes/09_demandes_credit.csv`

Grain : une demande déposée. C'est **la ligne de base du dataset de scoring** : une demande, une décision, un résultat éventuel.

| Colonne | Type | Domaine | Génération et dépendances | Rôle métier |
| --- | --- | --- | --- | --- |
| `identifiant_demande` | texte | `DEM-000001`… | — | clé primaire |
| `identifiant_client` | texte | clé étrangère | — | — |
| `identifiant_institution` | texte | clé étrangère | — | partition |
| `identifiant_agent` | texte | clé étrangère | agent en fonction à cette date dans l'agence du client | l'instructeur influe sur la décision |
| `identifiant_produit` | texte | clé étrangère | tirage selon `01_mix_produits`, filtré par les secteurs cibles et la date de lancement | l'orientation produit de l'institution se voit ici |
| `date_demande` | date | dans la fenêtre de relation | probabilité mensuelle = appétence latente × tension de trésorerie × absence de crédit actif × facteur d'ancienneté | horodatage de référence de toute variable de scoring |
| `montant_demande` | entier FCFA | bornes du produit | 1,5 à 3 fois les recettes mensuelles déclarées, × `multiplicateur_montant` de l'institution, arrondi à 5 000 | le client apprend à demander plus après un bon crédit |
| `duree_demandee_mois` | entier | bornes du produit | tirage pondéré, 6, 9 et 12 mois majoritaires | — |
| `objet_credit` | catégorie | `achat_stock`, `intrants`, `equipement`, `tresorerie`, `extension_activite` | cohérent avec le produit | lisibilité du dossier |
| `identifiant_releve_instruction` | texte | clé étrangère | le relevé produit le jour de la demande | **rend la fuite testable** : une variable ne peut lire que des relevés de date ≤ `date_demande` |
| `rang_demande_client` | entier | 1, 2, 3… | compteur des demandes antérieures | cycle de crédit, très discriminant en microfinance |

Une demande n'a **pas** de colonne de statut : la réponse est un fait distinct, avec sa propre date.

### 8.2 `brutes/10_decisions_credit.csv`

Table absente du plan initial, ajoutée ici : sans elle, un refus n'a nulle part où exister, et la reject inference devient impossible.

| Colonne | Type | Domaine | Génération et dépendances | Rôle métier |
| --- | --- | --- | --- | --- |
| `identifiant_decision` | texte | `DEC-000001`… | — | clé primaire |
| `identifiant_demande` | texte | clé étrangère, unique | relation 1–1 | — |
| `identifiant_institution` | texte | clé étrangère | — | partition |
| `date_decision` | date | `date_demande` + 1 à 21 jours | log-normale tronquée | délai d'instruction |
| `statut` | catégorie | `ACCEPTEE`, `REFUSEE`, `AJOURNEE`, `ANNULEE_CLIENT` | calibré sur `taux_acceptation_cible`, de 64 % à 86 % selon l'institution | la cible n'existe que pour les acceptées : tout le problème du biais de sélection |
| `motif_principal` | catégorie ou vide | `capacite_insuffisante`, `endettement_eleve`, `historique_incidents`, `activite_trop_recente`, `dossier_incomplet`, `garantie_insuffisante` | issu de la règle interne | explicabilité, et vérité terrain pour évaluer les explications d'un modèle |
| `montant_accorde` | entier FCFA ou vide | ≤ `montant_demande` | rationné de 10 à 40 % dans 30 % des acceptations | le rationnement est une décision réelle que le scoring doit pouvoir accompagner |
| `duree_accordee_mois` | entier ou vide | bornes du produit | égale à la durée demandée dans 85 % des cas | — |

La décision est prise par une règle interne combinant charge de dette, historique, ancienneté, cohérence du dossier, **la sévérité latente de l'agent** et **la sévérité de l'institution**. Cette règle n'est jamais publiée : sinon le modèle apprendrait la politique d'octroi au lieu du risque.

### 8.3 `brutes/11_credits.csv`

| Colonne | Type | Domaine | Génération |
| --- | --- | --- | --- |
| `identifiant_credit` | texte | `CRD-000001`… | un crédit n'existe que si la décision est `ACCEPTEE` |
| `identifiant_demande` | texte | clé étrangère, unique | traçabilité vers le dossier |
| `identifiant_institution` | texte | clé étrangère | partition |
| `date_decaissement` | date | `date_decision` + 0 à 14 jours | uniforme |
| `montant_decaisse` | entier FCFA | = `montant_accorde` | — |
| `duree_mois` | entier | = `duree_accordee_mois` | — |
| `type_amortissement` | catégorie | du produit | — |
| `differe_mois` | entier | 0, ou 4 à 6 en agricole | dépend du mois de décaissement par rapport au cycle de récolte |
| `echeance_theorique` | entier FCFA | calculée | arrondi à 25 F, l'écart étant absorbé par la dernière échéance |
| `date_premiere_echeance` | date | décaissement + périodicité + différé | — |
| `date_derniere_echeance_prevue` | date | cohérente avec la durée | fin d'observation attendue |

### 8.4 `brutes/12_echeances.csv`

Ce qui **devait** arriver.

| Colonne | Type | Domaine | Génération |
| --- | --- | --- | --- |
| `identifiant_echeance` | texte | `ECH-0000001`… | — |
| `identifiant_credit` | texte | clé étrangère | — |
| `identifiant_institution` | texte | clé étrangère | partition |
| `numero_echeance` | entier | 1 à N | séquentiel, sans trou |
| `date_exigible` | date | selon la périodicité | même quantième chaque mois, ramené au dernier jour du mois si nécessaire |
| `montant_capital_du` | entier FCFA | > 0 | selon le mode d'amortissement |
| `montant_interet_du` | entier FCFA | ≥ 0 | nul tant que le taux n'est pas arrêté (§6.6) |
| `montant_total_du` | entier FCFA | = capital + intérêt | somme exacte |

Invariant : `somme(montant_capital_du) = montant_decaisse`, exactement, pour chaque crédit.

### 8.5 `brutes/13_paiements.csv`

Ce qui **est réellement** arrivé. À ne jamais fusionner avec les échéances : c'est l'écart entre les deux qui porte toute l'information de risque.

| Colonne | Type | Domaine | Génération |
| --- | --- | --- | --- |
| `identifiant_paiement` | texte | `PAI-0000001`… | — |
| `identifiant_credit` | texte | clé étrangère | rattachement direct : un versement peut ne pas être affecté à une échéance précise |
| `identifiant_echeance` | texte ou vide | clé étrangère | vide pour un versement global de régularisation |
| `identifiant_institution` | texte | clé étrangère | partition |
| `date_paiement` | date | ≥ décaissement, ≤ fin du monde | issue du moteur de comportement |
| `montant_paye` | entier FCFA | > 0 | complet, partiel, ou multiple |
| `canal_paiement` | catégorie | `agence`, `mobile_money`, `collecteur` | 55 / 30 / 15, part du mobile money croissante sur la période |

Pas de colonne `jours_retard` : indicateur calculé, il appartient à `traitees/`.

Une échéance peut donner lieu à : aucun paiement, un paiement en avance, un paiement à l'heure, un paiement en retard, plusieurs paiements partiels, ou une régularisation tardive couvrant plusieurs échéances.

---

## 9. Couche 3 — `traitees/14_resultats_credit.csv`

Produite par déduction, jamais par tirage. Effacer le fichier et le recalculer doit redonner exactement le même résultat.

| Colonne | Type | Calcul |
| --- | --- | --- |
| `identifiant_credit` | texte | clé étrangère, unique |
| `identifiant_institution` | texte | partition |
| `date_arret_observation` | date | min(dernière échéance + 90 j, fin du monde) |
| `jours_retard_max` | entier | plus grand retard constaté |
| `nombre_echeances_impayees` | entier | échéances non soldées à la date d'arrêt |
| `capital_restant_du` | entier FCFA | — |
| `statut_final` | catégorie | `SOLDE`, `SOLDE_AVEC_RETARD`, `EN_COURS`, `DEFAUT_EXPERIMENTAL`, `RESTRUCTURE` |
| `defaut_experimental` | booléen | cible binaire |
| `date_survenue_defaut` | date ou vide | premier jour où la condition est remplie |
| `observation_censuree` | booléen | 1 si le crédit n'est pas arrivé à terme avant la fin du monde |

**Définition expérimentale du défaut** — un crédit est en défaut si, avant la date d'arrêt d'observation :

- une échéance atteint 90 jours de retard sans être soldée ; ou
- le remboursement est abandonné : trois échéances consécutives impayées et aucun versement pendant 120 jours ; ou
- le crédit est restructuré pour impayé persistant.

Étiquette de laboratoire. Elle devra être remplacée par la définition métier et prudentielle de l'institution partenaire avant tout usage réel.

**Censure** : les crédits décaissés tard n'ont pas eu le temps d'échouer. Ils portent `observation_censuree = 1` et sont **exclus de l'entraînement**. Recommandation : n'entraîner que sur les crédits décaissés jusqu'au 2025-03-31, et garder les suivants pour la validation hors période.

Cible de calibration : le taux de défaut observé de chaque institution doit tomber à ±2 points de son `taux_defaut_experimental_cible`. Si l'écart est plus grand, ce sont les paramètres du moteur de comportement qu'on corrige — jamais la définition du défaut.

---

## 10. Le reste du monde caché

| Fichier | Grain | Contenu |
| --- | --- | --- |
| `verite/03_profils_agents.csv` | agent | `severite` (Beta(4,4), décalée par l'institution), `qualite_saisie` qui pilote le taux de valeurs manquantes de ses relevés |
| `verite/05_parametres_secteurs.csv` | secteur | marge structurelle, amplitude saisonnière, mois de pic, volatilité de base |
| `verite/06_profils_latents.csv` | client | la personnalité financière, détaillée ci-dessous |
| `verite/07_parametres_activites.csv` | activité | niveau de recettes initial, marge, croissance, volatilité, saisonnalité |
| `verite/08_situations_mensuelles.csv` | activité × mois | le moteur économique (§7.4) |
| `verite/09_evenements.csv` | événement | chocs économiques individuels |
| `verite/09b_contexte_macro.csv` | mois × secteur | contexte économique du monde |
| `verite/10_decisions_contrefactuelles.csv` | demande refusée | ce qui se serait passé |
| `verite/qualite_injectee.csv` | cellule dégradée | journal des anomalies |
| `verite/manifeste_generation.json` | — | graine, version, empreintes SHA-256, indicateurs de contrôle |

### 10.1 `verite/06_profils_latents.csv`

| Colonne | Domaine | Loi | Rôle |
| --- | --- | --- | --- |
| `scenario_comportement` | `S01` à `S14` | parts du §12 | gabarit de personnalité |
| `code_personnage` | `CAS-001`… ou vide | non vide pour les 200 cas dorés | personnages déterministes |
| `discipline_paiement` | 0 à 1 | Beta(6,2) décalée de `decalage_discipline` | volonté de payer, indépendante de la capacité |
| `vulnerabilite_choc` | 0 à 1 | Beta(2,4) | sensibilité aux événements négatifs |
| `appetence_credit` | 0 à 1 | Beta(2,3) | fréquence de demande |
| `propension_sortie` | 0 à 0,05 | mensuelle | attrition |
| `coussin_epargne_initial` | ≥ 0 | corrélé à la discipline | absorbe les chocs avant l'impayé |

`discipline_paiement = 0.82` ne doit apparaître nulle part ailleurs que dans ce fichier.

### 10.2 `verite/09_evenements.csv`

Colonnes : `identifiant_evenement`, `identifiant_client`, `mois_debut`, `duree_mois`, `code_evenement`, `sens`, `intensite`, `source`.

Positifs : `hausse_activite`, `bonne_recolte`, `nouveau_contrat`, `elargissement_clientele`, `nouvel_equipement`, `desendettement`.
Négatifs : `baisse_ventes`, `mauvaise_recolte`, `perte_stock`, `fermeture_temporaire`, `hausse_charges`, `choc_secteur`, `depense_exceptionnelle`.

Le catalogue reste **strictement économique**. Aucun événement de santé, de famille ou de deuil : ces situations existent dans la réalité mais n'ont pas leur place dans un laboratoire de scoring, où elles finiraient par devenir des variables de décision.

Fréquence de base : 2,5 % par mois pour un événement négatif, modulée par `vulnerabilite_choc` ; 2 % pour un événement positif.

### 10.3 `verite/09b_contexte_macro.csv`

Colonnes : `mois`, `code_secteur`, `indice_activite`, `indice_charges`, `choc_actif`.

| Période | Contexte du scénario de base |
| --- | --- |
| 2021 | environnement normal |
| 2022 | normal, légère hausse des charges en fin d'année |
| 2023 | choc synthétique sur l'agriculture, indice d'activité 0,75 de juin à décembre |
| 2024 | reprise progressive |
| 2025 | hausse synthétique des charges sur tous les secteurs, indice 1,25 |

Chaque institution encaisse ce contexte à travers sa `sensibilite_macro` : `INS-002` le prend à 1,40, `INS-001` à 0,80. Le même choc mondial produit donc cinq histoires différentes.

Un modèle entraîné sur 2021–2023 et appliqué à 2025 doit se dégrader de façon mesurable. C'est le résultat attendu.

### 10.4 `verite/10_decisions_contrefactuelles.csv`

Le fichier scientifiquement le plus précieux du dépôt.

Colonnes : `identifiant_demande`, `aurait_ete_decaisse`, `defaut_contrefactuel`, `jours_retard_max_contrefactuel`, `capital_perdu_contrefactuel`.

Le simulateur déroule réellement le crédit refusé dans une branche parallèle du monde, avec le même flux aléatoire, puis écarte le résultat des tables observables. Cela permet de mesurer ce qu'aucune institution réelle ne peut mesurer : **la qualité des refus**. Et donc d'évaluer honnêtement une méthode de reject inference.

---

## 11. Dégradation volontaire des données

Une base réelle n'est jamais propre. La dégradation intervient **après** la génération d'un monde cohérent, et elle est intégralement tracée dans `verite/qualite_injectee.csv` (`table_cible`, `identifiant_ligne`, `colonne`, `type_anomalie`, `valeur_vraie`, `valeur_publiee`).

| Type d'anomalie | Cible | Taux de base | Intention |
| --- | --- | --- | --- |
| `valeur_manquante` | relevés, épargne | 6 % | traiter l'absence sans la confondre avec un zéro |
| `doublon_ligne` | relevés, paiements | 0,8 % | détecter les doublons de saisie |
| `date_incoherente` | relevé postérieur à la demande, paiement antérieur au décaissement | 0,5 % | l'incohérence chronologique est la plus dangereuse : elle crée une fuite |
| `montant_aberrant` | recettes ou charges × 10 ou × 100 | 0,4 % | erreur d'unité |
| `categorie_erronee` | secteur incohérent avec le libellé d'activité | 1 % | mauvaise catégorisation |
| `incoherence_economique` | charges déclarées supérieures aux recettes | 1,5 % | **cas ambigu volontaire** |
| `arrondi_suspect` | recettes rondes à 100 000 près | 3 % | déclaration approximative |

Tous ces taux sont multipliés par le `facteur_qualite_donnees` de l'institution : de 0,70 pour `INS-001` à 1,80 pour `INS-005`. Une même chaîne de nettoyage rencontrera donc des bases de qualités très différentes — ce qui est précisément ce qu'on veut éprouver.

`charges = 850 000` avec `recettes = 120 000` **n'est pas nécessairement une erreur** : cela peut décrire un mois de réapprovisionnement, une perte réelle, ou une saisie fausse. Le module de qualité doit apprendre à distinguer la donnée *improbable* — qu'on signale et qu'on garde — de la donnée *impossible* — un paiement daté avant le décaissement — qu'on rejette.

Deux garde-fous : l'intégrité référentielle n'est **jamais** dégradée, et les clés primaires ne sont jamais altérées. Sinon les jointures cassent pour de mauvaises raisons.

---

## 12. Bibliothèque de scénarios de comportement

Remarque de méthode : les vingt scénarios envisagés ne sont pas de même nature, et les traiter comme vingt boîtes exclusives fabriquerait un monde faux.

| Nature | Scénarios | Traitement |
| --- | --- | --- |
| Personnalité économique | S01 à S14 | **exclusifs**, un seul par client, avec variabilité interne |
| Qualité de données | S15, S16 | **couche transverse** appliquée après coup (§11) |
| Modalités de paiement | S17, S18 | **conséquences émergentes**, jamais imposées |
| Trajectoire de relation | S19, S20 | **résultats émergents** du moteur de demande et de décision |

Un client peut donc être S02, subir une injection de données incomplètes, produire des paiements partiels et enchaîner quatre crédits — sans qu'aucune de ces trois dernières propriétés ne soit une étiquette tirée au sort.

| Code | Scénario | Contraintes latentes | Part visée |
| --- | --- | --- | --- |
| S01 | Excellent payeur | discipline > 0,90 ; volatilité < 0,15 | 8 % |
| S02 | Payeur normal | discipline 0,70–0,90 | 28 % |
| S03 | Retards occasionnels | discipline 0,55–0,70 | 12 % |
| S04 | Retards fréquents | discipline 0,35–0,55 | 8 % |
| S05 | Défaut précoce | discipline < 0,35 ; vulnérabilité > 0,60 | 2 % |
| S06 | Défaut après plusieurs bons crédits | discipline > 0,75 puis choc au 3ᵉ ou 4ᵉ crédit | 3 % |
| S07 | Nouveau client sans historique | entrée dans les 12 derniers mois | 7 % |
| S08 | Fortes recettes, faible marge | niveau > P75 ; marge < 0,10 | 4 % |
| S09 | Faibles recettes, forte marge | niveau < P25 ; marge > 0,35 | 5 % |
| S10 | Endettement croissant | `dette_externe_mensualite` croissante | 4 % |
| S11 | Activité très saisonnière | amplitude > 0,45 | 5 % |
| S12 | Revenus très volatils | volatilité > 0,40 | 5 % |
| S13 | Amélioration progressive | croissance > +0,15 | 4 % |
| S14 | Dégradation progressive | croissance < −0,10 | 5 % |

Total 100 %. Ces parts sont celles de l'institution de référence `INS-004` ; les autres les déforment via `decalage_discipline` et `decalage_volatilite`. À l'intérieur d'un scénario, les paramètres restent tirés dans leur plage : deux clients S03 ne se ressemblent pas. La liste est extensible — ajouter S21 consiste à décrire des contraintes, pas à écrire du code particulier.

### Cas dorés

Quarante personnages déterministes par institution, soit 200, identifiants `CLT-000001` à `CLT-000200`, décrits un par un dans `simulation/configuration/personnages.yaml`. Générés en premier, avec un flux aléatoire dédié, et **exclus des injections d'anomalies** — sauf ceux dont le rôle est précisément d'avoir un dossier incomplet.

| Code | Personnage | Rôle pédagogique |
| --- | --- | --- |
| CAS-001 | Fatou | trajectoire saine : activité stable, premier crédit excellent, petit retard au deuxième, croissance, grosse demande en 2025 |
| CAS-002 | Ibrahim | le piège : recettes élevées, charges énormes, marge faible, endettement externe croissant |
| CAS-003 | Awa | données insuffisantes : entrée récente, un seul relevé, aucun historique de crédit |
| CAS-004 … | — | un cas par situation limite à couvrir dans les tests et la démonstration |

Leur comportement ne doit jamais changer d'une génération à l'autre : c'est le test de non-régression du monde lui-même.

---

## 13. Scénarios de monde

Le dépôt ne produit pas un jeu de données mais **une usine à jeux de données**. Chaque scénario surcharge les paramètres de base sans jamais changer la structure des tables.

```bash
python simulation/generer.py --graine 7
python simulation/generer.py --scenario stress_agricole
```

| Scénario | Ce qu'il change | Ce qu'il éprouve |
| --- | --- | --- |
| `scenario_base.yaml` | référence du présent document | comportement nominal |
| `scenario_stress_agricole.yaml` | choc agricole prolongé 2023–2025 | robustesse sectorielle, surtout sur `INS-002` |
| `scenario_crise.yaml` | tous secteurs dégradés en 2024 | dérive brutale |
| `scenario_croissance.yaml` | tendance positive généralisée | sous-estimation du risque en période faste |
| `scenario_donnees_degradees.yaml` | taux d'anomalies × 3 | résistance du pipeline à une base sale |

---

## 14. Relations et invariants vérifiables

```text
institutions ──< agences ──< agents_credit ──< demandes_credit
institutions ──< agences ──< clients ──< activites ──< releves_activite
                                             └──< situations_mensuelles (vérité)
clients ──< demandes_credit ──1:1── decisions_credit
                    └──1:0..1── credits ──< echeances ──< paiements
produits_credit ──< demandes_credit          secteurs_activite ──< activites
```

Tests obligatoires avant toute publication d'un jeu de données :

1. Toute clé étrangère pointe vers une ligne existante.
2. `identifiant_institution` est cohérent tout au long de la chaîne : le client, son agence, son agent, sa demande et son crédit appartiennent tous à la même institution.
3. Chaque mix sectoriel et chaque mix produits somme à 1,0000 par institution.
4. La `specialisation_principale` annoncée correspond au secteur dominant du mix latent, sauf `DIVERSIFIE`.
5. Tout code secteur et tout code produit référencé dans un mix existe dans son référentiel.
6. Une décision par demande, exactement. Un crédit seulement pour une décision `ACCEPTEE`, et un seul par demande.
7. `date_demande ≤ date_decision ≤ date_decaissement ≤ date_premiere_echeance`.
8. Aucun paiement antérieur au décaissement de son crédit, hors anomalies déclarées dans `qualite_injectee`.
9. Le nombre d'échéances d'un crédit égale sa durée, sans trou de numérotation, et `somme(capital_du) = montant_decaisse`.
10. `montant_accorde ≤ montant_demande`, les deux dans les bornes du produit.
11. Aucun événement, relevé ou demande hors de la fenêtre de relation du client ; aucune date hors de l'horizon du monde.
12. Aucun client rattaché à une agence non encore ouverte, ni instruit par un agent hors fonction.
13. Aucune colonne de `verite/` ne porte le même nom qu'une colonne de `brutes/`, hors clés de jointure.
14. Pour chaque demande, tous les relevés utilisables ont une `date_releve ≤ date_demande`.
15. Le taux d'acceptation et le taux de défaut de chaque institution tombent à ±2 points de leur cible.
16. Deux générations de même graine produisent des empreintes SHA-256 identiques.
17. Aucun cahier de `laboratoires/` ne lit `donnees/synthetiques/verite/`, hors cahier d'évaluation explicitement autorisé.

---

## 15. Ce qui n'est pas couvert

- **Le dictionnaire des variables de scoring** (`variables/scoring_credit.csv`) : une ligne par demande, construite uniquement à partir de faits datés strictement avant `date_demande`. Document 08 à venir : il relève de la modélisation, pas de la description du monde.
- **Le taux d'intérêt et la tarification**, tant qu'aucun paramètre défendable et sourcé n'est disponible (§6.6).
- **Le crédit solidaire de groupe**, pourtant central en microfinance : il suppose de modéliser des groupes et une caution mutuelle. Extension identifiée.
- **L'épargne comme flux** : seul le solde à l'entrée en relation est simulé.
- **Les garanties et leur réalisation.**
- **Les rééchelonnements négociés** autres que la restructuration pour impayé.

---

## 16. Étapes suivantes

1. ✅ Couches 01 à 14, plus la dégradation volontaire et les contrôles du §14 (`tests/verifier_monde.py`).
2. ✅ Première génération contrôlée : `INS-001`, 100 clients, 39 contrôles passés, reproductible octet pour octet.
3. Écrire `personnages.yaml` : les cas dorés, dont Fatou, Ibrahim et Awa.
4. Arrêter la question du taux d'intérêt, ou assumer explicitement le taux nul dans toute communication (§6.6).
5. Générer les cinq institutions à 10 000 clients et confronter les volumes réels aux ordres de grandeur du §4, puis trancher le format de stockage de `08_situations_mensuelles`.
6. Vérifier que les cinq mondes se comportent bien différemment : taux de défaut, saisonnalité, longueur des historiques, qualité des données.
7. Document 08 : le dictionnaire des variables de scoring, construit sous la contrainte anti-fuite du §14.
