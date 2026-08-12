# Dictionnaire des données synthétiques

Les neuf CSV sous `donnees/synthetiques/brutes/` forment la source de vérité de la SFD fictive. Ils sont générés par `simulation/generer.py`, versionnés, et ne sont jamais modifiés manuellement.

## Référentiels

### `agences.csv`

| Colonne | Description |
| --- | --- |
| `identifiant_agence` | Identifiant stable, par exemple `AGC-001` |
| `nom_agence` | Nom fictif de l'agence |
| `ville` | Ville fictive d'implantation |
| `date_ouverture` | Date d'ouverture simulée |

### `agents_credit.csv`

| Colonne | Description |
| --- | --- |
| `identifiant_agent` | Identifiant stable, par exemple `AGT-007` |
| `identifiant_agence` | Référence vers `agences.csv` |
| `nom_agent` | Nom fictif de l'agent |
| `date_entree_fonction` | Début d'activité simulé |

### `produits_credit.csv`

| Colonne | Description |
| --- | --- |
| `identifiant_produit` | Identifiant stable du produit |
| `code_produit` | Code court, par exemple `STOCK` |
| `nom_produit` | Libellé métier du produit |
| `montant_min`, `montant_max` | Bornes fictives du montant |
| `duree_min_mois`, `duree_max_mois` | Bornes fictives de durée |

## Vie du client et crédit

### `clients.csv`

`identifiant_client`, `identifiant_agence`, `secteur_activite`, `date_entree`, `profil_synthetique`.

### `activites.csv`

`identifiant_activite`, `identifiant_client`, `mois`, `chiffre_affaires`, `charges_activite`, `saisonnalite`.

### `demandes_credit.csv`

`identifiant_demande`, `identifiant_client`, `identifiant_agent`, `identifiant_produit`, `date_demande`, `montant_demande`, `duree_mois`, `statut`.

### `credits.csv`

`identifiant_credit`, `identifiant_demande`, `date_decaissement`, `montant_decaisse`, `duree_mois`, `echeance_mensuelle`.

### `echeances.csv`

`identifiant_echeance`, `identifiant_credit`, `numero`, `date_exigible`, `montant_du`.

### `paiements.csv`

`identifiant_paiement`, `identifiant_echeance`, `date_paiement`, `montant_paye`, `jours_retard`.

## Relations obligatoires

```text
agences → agents_credit → demandes_credit
agences → clients → activites
clients → demandes_credit → credits → echeances → paiements
produits_credit → demandes_credit
```

Chaque lien est vérifié par le futur générateur : aucune demande sans client/agent/produit, aucun crédit sans demande acceptée, aucune échéance sans crédit et aucun paiement sans échéance.
