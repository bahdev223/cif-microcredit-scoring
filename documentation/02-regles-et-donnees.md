# Regles et donnees

## Données connues à la décision

| Donnee | Utilite |
| --- | --- |
| Montant demande | Estimer l'echeance indicative |
| Revenu et charges | Estimer la capacite de remboursement |
| Anciennete d'activite | Mesurer le recul sur l'activite |
| Retards precedents | Signaler un risque de remboursement |
| Regularite tontine | Indice complementaire de discipline financiere |

## Historique importé

Les crédits antérieurs, échéances, paiements et retards proviennent du système existant de l'institution. Ils sont observés pour construire des indicateurs comme le nombre de crédits soldés, le nombre de retards, le retard maximal ou l'ancienneté de relation. Ils ne sont pas saisis comme opérations de caisse dans notre plateforme.

## Résultat observé

Après une décision, un nouvel export peut apporter les paiements réellement observés. Ces résultats servent à évaluer le modèle et, plus tard, à envisager un réentraînement contrôlé. Les informations postérieures à la décision ne doivent jamais être utilisées comme variables disponibles à T0.

## Identification n'est pas scoring

Les données nécessaires au rattachement d'un dossier ne deviennent pas automatiquement des variables de scoring. Le nom, le téléphone ou l'identifiant source servent à retrouver et rapprocher le client ; ils ne sont pas des features du modèle.

Les caractéristiques personnelles facultatives — âge, sexe, localité, agence ou type de client — sont **interdites comme features par défaut**. Leur éventuelle utilisation devrait être explicitement justifiée, validée et conforme au cadre applicable.

## Gouvernance des variables

Chaque champ du schéma canonique doit être documenté avec : sa description, son type, son caractère obligatoire, sa source, son rôle (identification, analyse métier, feature candidate, outcome ou audit), son caractère personnel ou sensible, sa justification et sa durée de conservation à définir.

`FEATURE_SCORING = false` est la valeur par défaut. Une variable doit démontrer qu'elle est disponible à T0, utile, fiable, légitime et non discriminatoire avant toute entrée dans un modèle.

## Regles simples

- R01 : si la capacite mensuelle est inferieure a l'echeance indicative, lever une alerte.
- R02 : si l'activite a moins de 12 mois, signaler une anciennete faible.
- R03 : si des retards sont declares, signaler l'historique a l'agent.

Le score de 0 a 100 est uniquement un indicateur de demonstration. Il combine ces signaux de facon explicable ; il ne represente pas une probabilite statistique de defaut.

## Qualite et protection des donnees

Les donnees de demo sont fictives. Pour une version reelle : consentement, minimisation des donnees, pseudonymisation, chiffrement, acces par role et journal d'audit seront obligatoires. La collecte doit etre validee avec l'institution et les regles applicables dans le pays concerne.
