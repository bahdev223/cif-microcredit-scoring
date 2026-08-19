# API du prototype

Base locale : `http://127.0.0.1:8000`

## Etat du service

`GET /api/etat/`

Reponse :

```json
{"etat":"operationnel","service":"evaluation-microcredit-cif"}
```

## Analyser une demande de credit

`POST /api/demandes-credit/analyser/`

```json
{
  "nom_complet": "Fatou Traore",
  "secteur_activite": "Commerce",
  "revenu_mensuel": 180000,
  "charges_mensuelles": 65000,
  "anciennete_activite_mois": 36,
  "nombre_retards": 0,
  "regularite_tontine": "reguliere",
  "montant_demande": 300000,
  "duree_mois": 12
}
```

Les valeurs de `regularite_tontine` sont `reguliere`, `partielle` ou `inconnue`. La reponse contient `score_risque`, `niveau_risque`, `recommandation` et `explication`. Chaque appel valide cree aussi un journal d'audit.

Exemple Windows PowerShell :

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/demandes-credit/analyser/ -ContentType 'application/json' -Body '{"nom_complet":"Fatou Traore","secteur_activite":"Commerce","revenu_mensuel":180000,"charges_mensuelles":65000,"anciennete_activite_mois":36,"nombre_retards":0,"regularite_tontine":"reguliere","montant_demande":300000}'
```

## Institution

- `GET /api/institution/` : retourne le nom, le sigle, la ville et le pays configurés ;
- `POST /api/institution/enregistrer/` : enregistre la configuration unique de la démo.

```json
{"nom":"CIF Microfinance","sigle":"CIF","ville":"Bamako","pays":"Mali"}
```

## Clients

- `GET /api/clients/` : liste les 100 derniers clients ;
- `POST /api/clients/creer/` : enregistre un client.
- `GET /api/clients/<identifiant>/` : retourne le dossier consolidé, avec activités, demandes, crédits, échéances et paiements observés ;
- `PUT /api/clients/<identifiant>/modifier/` : modifie les informations du client ;
- `DELETE /api/clients/<identifiant>/supprimer/` : supprime le client lorsque ses relations le permettent.

Le corps de création reprend les informations financières du client utilisées dans l'analyse : `nom_complet`, `secteur_activite`, `revenu_mensuel`, `charges_mensuelles`, `anciennete_activite_mois`, avec en complément `mensualite_dette_existante`, `nombre_retards` et `regularite_tontine` si connus.

## Demandes déjà enregistrées

`GET /api/demandes-credit/` retourne les 100 dernières demandes, leur client, montant, durée, score et niveau de risque.

Pour analyser une nouvelle demande d'un client déjà enregistré, envoyer `identifiant_client` avec `montant_demande` et `duree_mois` à `POST /api/demandes-credit/analyser/`. Les autres champs client ne sont alors pas nécessaires et aucun doublon de client n'est créé.

## Import historique

Les routes d'import reçoivent un lot CSV, vérifient sa structure puis persistent les données historiques : clients, activités, demandes source, crédits, échéances et paiements.

- `GET /api/imports-csv/lots/` : référentiel des fichiers attendus ;
- `POST /api/imports-csv/valider/` : lecture, contrôle de format, colonnes, types et relations ;
- `POST /api/imports-csv/confirmer/` : import après validation.

Ces routes n'encaisseront jamais un paiement et ne décaissent jamais un crédit. Elles servent à acquérir et observer l'historique fourni par le système existant.

## Acquisition Excel/CSV avec mapping humain

Le parcours d'acquisition assisté est celui utilisé par l'écran **Données → Importer des données**. Il ne remplace pas les routes de lot CSV normalisé : il prépare un export institutionnel dont les noms de colonnes sont différents de ceux de CIF.

- `POST /api/acquisition/analyser-fichier/` : reçoit `fichier` et, pour Excel, `feuille` facultative ; retourne les feuilles, l'aperçu, les propositions de table et de correspondance ; aucune écriture.
- `POST /api/acquisition/valider-correspondance/` : reçoit `fichier`, `feuille` facultative et `correspondance` JSON ; retourne le tableau normalisé, les anomalies et les six dimensions de qualité ; aucune écriture.
- `POST /api/acquisition/valider-lot/` : reçoit plusieurs champs `fichiers` et un tableau JSON `correspondances` dans le même ordre ; contrôle les relations inter-tables et retourne un diagnostic de préparation au scoring ; aucune écriture.
- `POST /api/acquisition/confirmer-lot/` : même contrat que la validation ; persiste uniquement le lot sans erreur bloquante, puis les clients et leur historique deviennent visibles dans le dossier client.

Un fichier correspond à une table canonique : `clients`, `activites`, `demandes_credit`, `credits`, `echeances` ou `paiements`. Le mapping est toujours choisi ou confirmé par un humain. Le diagnostic peut signaler **Dataset à préparer** ou **Exploration possible**, mais ne dit jamais qu'un modèle est prêt : il manque encore la cible de défaut validée et les variables T0.

## API d'ingestion cible — non livrée

La future API d'intégration pourra exposer un lot canonique, par exemple `POST /api/v1/ingestion/lots/`, ou des ressources telles que `clients`, `activites`, `demandes`, `credits`, `echeances` et `paiements`.

Cette notation est une intention d'architecture, pas une route actuellement disponible. Avant implémentation, le contrat devra être défini dans `15-schema-canonique-v1.md`. Chaque requête devra suivre le pipeline commun : mapping, validation de schéma, validation relationnelle, Data Quality, normalisation, aperçu puis persistance. Aucun endpoint ne doit écrire directement dans la base en contournant ces étapes.
