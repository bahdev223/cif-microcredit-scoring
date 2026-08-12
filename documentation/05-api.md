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

Le corps de création reprend les informations financières du client utilisées dans l'analyse : `nom_complet`, `secteur_activite`, `revenu_mensuel`, `charges_mensuelles`, `anciennete_activite_mois`, avec en complément `mensualite_dette_existante`, `nombre_retards` et `regularite_tontine` si connus.

## Demandes déjà enregistrées

`GET /api/demandes-credit/` retourne les 100 dernières demandes, leur client, montant, durée, score et niveau de risque.

Pour analyser une nouvelle demande d'un client déjà enregistré, envoyer `identifiant_client` avec `montant_demande` et `duree_mois` à `POST /api/demandes-credit/analyser/`. Les autres champs client ne sont alors pas nécessaires et aucun doublon de client n'est créé.
