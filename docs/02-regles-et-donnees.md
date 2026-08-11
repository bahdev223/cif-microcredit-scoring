# Regles et donnees

## Donnees V0

| Donnee | Utilite |
| --- | --- |
| Montant demande | Estimer l'echeance indicative |
| Revenu et charges | Estimer la capacite de remboursement |
| Anciennete d'activite | Mesurer le recul sur l'activite |
| Retards precedents | Signaler un risque de remboursement |
| Regularite tontine | Indice complementaire de discipline financiere |

## Regles simples

- R01 : si la capacite mensuelle est inferieure a l'echeance indicative, lever une alerte.
- R02 : si l'activite a moins de 12 mois, signaler une anciennete faible.
- R03 : si des retards sont declares, signaler l'historique a l'agent.

Le score de 0 a 100 est uniquement un indicateur de demonstration. Il combine ces signaux de facon explicable ; il ne represente pas une probabilite statistique de defaut.

## Qualite et protection des donnees

Les donnees de demo sont fictives. Pour une version reelle : consentement, minimisation des donnees, pseudonymisation, chiffrement, acces par role et journal d'audit seront obligatoires. La collecte doit etre validee avec l'institution et les regles applicables dans le pays concerne.
