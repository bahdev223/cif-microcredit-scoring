import json
import csv
from io import StringIO

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from audit.models import JournalAudit
from clients.models import Client, Institution
from credits.models import CreditImporte, DemandeCredit, EcheanceImportee, PaiementImporte
from evaluation_risque.explicabilite import expliquer_prediction
from evaluation_risque.predicteur import predire_risque

FICHIERS_IMPORT = {
    "clients.csv": {"identifiant_client", "identifiant_institution", "code_secteur_principal", "anciennete_activite_mois_a_entree"},
    "activites.csv": {"identifiant_activite", "identifiant_client", "identifiant_institution"},
    "demandes_credit.csv": {"identifiant_demande", "identifiant_client", "identifiant_institution", "montant_demande", "duree_demandee_mois"},
    "credits.csv": {"identifiant_credit", "identifiant_demande", "identifiant_institution"},
    "echeances.csv": {"identifiant_echeance", "identifiant_credit", "identifiant_institution"},
    "paiements.csv": {"identifiant_paiement", "identifiant_credit", "identifiant_echeance", "identifiant_institution"},
}


def lire_csv_importe(fichier):
    texte = fichier.read().decode("utf-8-sig")
    lecteur = csv.DictReader(StringIO(texte))
    if not lecteur.fieldnames:
        raise ValueError(f"{fichier.name} ne contient pas d'en-têtes.")
    lignes = list(lecteur)
    manquantes = sorted(FICHIERS_IMPORT[fichier.name] - set(lecteur.fieldnames))
    return lignes, manquantes


def analyser_lot_import(requete):
    fichiers = {fichier.name: fichier for fichier in requete.FILES.getlist("fichiers")}
    erreurs, avertissements, anomalies, tables = [], [], [], {}
    for nom in FICHIERS_IMPORT:
        if nom not in fichiers:
            erreurs.append(f"{nom} est manquant.")
            continue
        try:
            lignes, manquantes = lire_csv_importe(fichiers[nom])
            tables[nom] = lignes
            if manquantes:
                erreurs.append(f"{nom} : colonnes manquantes — {', '.join(manquantes)}.")
                anomalies.append({"fichier": nom, "ligne": 1, "type": "Colonnes manquantes", "detail": ", ".join(manquantes)})
            if not lignes:
                erreurs.append(f"{nom} ne contient aucune ligne.")
        except (UnicodeDecodeError, ValueError) as erreur:
            erreurs.append(str(erreur))

    if tables.get("clients.csv"):
        clients = tables["clients.csv"]
        identifiants = [ligne.get("identifiant_client", "") for ligne in clients]
        if len(identifiants) != len(set(identifiants)):
            erreurs.append("clients.csv contient des identifiants client dupliqués.")
            vus = set()
            for numero, identifiant in enumerate(identifiants, start=2):
                if identifiant in vus:
                    anomalies.append({"fichier": "clients.csv", "ligne": numero, "type": "Doublon", "detail": identifiant})
                vus.add(identifiant)
        manquants = sum(1 for ligne in clients for valeur in ligne.values() if not valeur)
        if manquants:
            avertissements.append(f"{manquants} valeur(s) manquante(s) détectée(s) dans clients.csv.")
            for numero, ligne in enumerate(clients, start=2):
                for colonne, valeur in ligne.items():
                    if not valeur:
                        anomalies.append({"fichier": "clients.csv", "ligne": numero, "type": "Valeur manquante", "detail": colonne})

    relations = [
        ("activites.csv", "identifiant_client", "clients.csv", "identifiant_client"),
        ("demandes_credit.csv", "identifiant_client", "clients.csv", "identifiant_client"),
        ("credits.csv", "identifiant_demande", "demandes_credit.csv", "identifiant_demande"),
        ("echeances.csv", "identifiant_credit", "credits.csv", "identifiant_credit"),
        ("paiements.csv", "identifiant_credit", "credits.csv", "identifiant_credit"),
        ("paiements.csv", "identifiant_echeance", "echeances.csv", "identifiant_echeance"),
    ]
    for enfant, cle_enfant, parent, cle_parent in relations:
        if enfant in tables and parent in tables:
            connus = {ligne.get(cle_parent) for ligne in tables[parent]}
            incoherentes = [ligne.get(cle_enfant) for ligne in tables[enfant] if ligne.get(cle_enfant) not in connus]
            if incoherentes:
                erreurs.append(f"{enfant} : {len(incoherentes)} relation(s) invalide(s) vers {parent}.")
                for numero, ligne in enumerate(tables[enfant], start=2):
                    if ligne.get(cle_enfant) not in connus:
                        anomalies.append({"fichier": enfant, "ligne": numero, "type": "Relation invalide", "detail": f"{cle_enfant}={ligne.get(cle_enfant)}"})

    total = sum(len(lignes) for lignes in tables.values())
    qualite = max(0, 100 - 20 * len(erreurs) - 3 * len(avertissements))
    return tables, erreurs, avertissements, anomalies[:100], total, qualite


def nom_fictif(identifiant):
    prenoms = ("Fatou", "Awa", "Ibrahim", "Mariam", "Ousmane", "Aminata", "Moussa", "Kadiatou")
    noms = ("Traoré", "Diallo", "Coulibaly", "Koné", "Camara", "Keïta", "Touré", "Diarra")
    numero = int(identifiant.split("-")[-1])
    return f"{prenoms[numero % len(prenoms)]} {noms[(numero // len(prenoms)) % len(noms)]} {numero:03d}"


@csrf_exempt
@require_POST
def valider_import_csv(requete):
    try:
        tables, erreurs, avertissements, anomalies, total, qualite = analyser_lot_import(requete)
    except Exception as erreur:
        return JsonResponse({"erreur": f"Lecture impossible : {erreur}"}, status=400)
    return JsonResponse({
        "valide": not erreurs,
        "qualite": qualite,
        "erreurs": erreurs,
        "avertissements": avertissements,
        "anomalies": anomalies,
        "lignes": {nom: len(lignes) for nom, lignes in tables.items()},
        "total_lignes": total,
    })


@csrf_exempt
@require_POST
def confirmer_import_csv(requete):
    try:
        tables, erreurs, avertissements, anomalies, total, qualite = analyser_lot_import(requete)
    except Exception as erreur:
        return JsonResponse({"erreur": f"Lecture impossible : {erreur}"}, status=400)
    if erreurs:
        return JsonResponse({"erreur": "Le lot contient des erreurs et ne peut pas être importé.", "erreurs": erreurs}, status=400)

    clients_par_source = {}
    ajoutes = 0
    for ligne in tables["clients.csv"]:
        client, cree = Client.objects.update_or_create(
            identifiant_source=ligne["identifiant_client"],
            defaults={
                "nom_complet": nom_fictif(ligne["identifiant_client"]),
                "identifiant_institution_source": ligne.get("identifiant_institution", ""),
                "secteur_activite": ligne.get("code_secteur_principal", "Non renseigné").replace("_", " ").title(),
                "revenu_mensuel": 0, "charges_mensuelles": 0,
                "anciennete_activite_mois": int(ligne.get("anciennete_activite_mois_a_entree") or 0),
                "nombre_retards": 0, "regularite_tontine": "inconnue",
            },
        )
        clients_par_source[ligne["identifiant_client"]] = client
        ajoutes += int(cree)

    demandes = {ligne["identifiant_demande"]: ligne for ligne in tables["demandes_credit.csv"]}
    credits_par_source = {}
    for ligne in tables["credits.csv"]:
        demande = demandes.get(ligne.get("identifiant_demande"), {})
        client = clients_par_source.get(demande.get("identifiant_client"))
        if client:
            credit, _ = CreditImporte.objects.update_or_create(
                identifiant_source=ligne["identifiant_credit"],
                defaults={"client": client, "identifiant_demande_source": ligne.get("identifiant_demande", ""),
                          "montant_decaisse": int(ligne.get("montant_decaisse") or 0),
                          "duree_mois": int(ligne.get("duree_mois") or 0),
                          "date_decaissement": ligne.get("date_decaissement") or None},
            )
            credits_par_source[ligne["identifiant_credit"]] = credit
    echeances_par_source = {}
    for ligne in tables["echeances.csv"]:
        credit = credits_par_source.get(ligne.get("identifiant_credit"))
        if credit:
            echeance, _ = EcheanceImportee.objects.update_or_create(
                identifiant_source=ligne["identifiant_echeance"],
                defaults={"credit": credit, "numero": int(ligne.get("numero_echeance") or 0),
                          "date_exigible": ligne.get("date_exigible") or None,
                          "montant_du": int(ligne.get("montant_total_du") or 0)},
            )
            echeances_par_source[ligne["identifiant_echeance"]] = echeance
    for ligne in tables["paiements.csv"]:
        credit = credits_par_source.get(ligne.get("identifiant_credit"))
        if credit:
            PaiementImporte.objects.update_or_create(
                identifiant_source=ligne["identifiant_paiement"],
                defaults={"credit": credit, "echeance": echeances_par_source.get(ligne.get("identifiant_echeance")),
                          "date_paiement": ligne.get("date_paiement") or None,
                          "montant_paye": int(ligne.get("montant_paye") or 0), "canal": ligne.get("canal_paiement", "")},
            )
    return JsonResponse({"message": "Import confirmé.", "clients_ajoutes": ajoutes, "credits_importes": len(credits_par_source), "qualite": qualite, "avertissements": avertissements, "total_lignes": total})


@require_GET
def detail_client(requete, identifiant_client):
    try:
        client = Client.objects.get(pk=identifiant_client)
    except Client.DoesNotExist:
        return JsonResponse({"erreur": "Client introuvable."}, status=404)
    credits = client.credits_importes.prefetch_related("echeances", "paiements").all()
    return JsonResponse({"client": serialiser_client(client), "credits": [{
        "identifiant": credit.identifiant_source, "montant": credit.montant_decaisse,
        "duree_mois": credit.duree_mois, "date_decaissement": credit.date_decaissement.isoformat() if credit.date_decaissement else "",
        "echeances": [{"numero": e.numero, "date": e.date_exigible.isoformat() if e.date_exigible else "", "montant": e.montant_du} for e in credit.echeances.all()],
        "paiements": [{"date": p.date_paiement.isoformat() if p.date_paiement else "", "montant": p.montant_paye, "canal": p.canal} for p in credit.paiements.all()],
    } for credit in credits]})


@require_GET
def etat_service(requete):
    return JsonResponse({"etat": "operationnel", "service": "evaluation-microcredit-cif"})


def lire_json(requete):
    try:
        return json.loads(requete.body)
    except json.JSONDecodeError as erreur:
        raise ValueError(f"JSON invalide : {erreur.msg}") from erreur


def serialiser_client(client):
    return {
        "identifiant": client.id,
        "nom_complet": client.nom_complet,
        "secteur_activite": client.secteur_activite,
        "revenu_mensuel": client.revenu_mensuel,
        "charges_mensuelles": client.charges_mensuelles,
        "mensualite_dette_existante": client.mensualite_dette_existante,
        "anciennete_activite_mois": client.anciennete_activite_mois,
        "nombre_retards": client.nombre_retards,
        "regularite_tontine": client.regularite_tontine,
        "cree_le": client.cree_le.isoformat(),
    }


@csrf_exempt
@require_GET
def liste_clients(requete):
    return JsonResponse({"clients": [serialiser_client(client) for client in Client.objects.order_by("-cree_le")[:100]]})


@csrf_exempt
@require_POST
def creer_client(requete):
    try:
        donnees = lire_json(requete)
        client = Client.objects.create(
            nom_complet=donnees["nom_complet"].strip(),
            secteur_activite=donnees["secteur_activite"].strip(),
            revenu_mensuel=int(donnees["revenu_mensuel"]),
            charges_mensuelles=int(donnees["charges_mensuelles"]),
            mensualite_dette_existante=int(donnees.get("mensualite_dette_existante", 0)),
            anciennete_activite_mois=int(donnees["anciennete_activite_mois"]),
            nombre_retards=int(donnees.get("nombre_retards", 0)),
            regularite_tontine=donnees.get("regularite_tontine", "inconnue"),
        )
    except (KeyError, TypeError, ValueError) as erreur:
        return JsonResponse({"erreur": f"Données invalides : {erreur}"}, status=400)
    return JsonResponse({"client": serialiser_client(client)}, status=201)


@csrf_exempt
@require_GET
def liste_demandes_credit(requete):
    demandes = DemandeCredit.objects.select_related("client").order_by("-cree_le")[:100]
    return JsonResponse({"demandes": [{
        "identifiant": demande.id,
        "client": demande.client.nom_complet,
        "montant_demande": demande.montant_demande,
        "duree_mois": demande.duree_mois,
        "score_risque": demande.score_risque,
        "niveau_risque": demande.niveau_risque,
        "decision_agent": demande.decision_agent,
        "cree_le": demande.cree_le.isoformat(),
    } for demande in demandes]})


@csrf_exempt
@require_GET
def lire_institution(requete):
    institution, _ = Institution.objects.get_or_create(pk=1)
    return JsonResponse({"institution": {"nom": institution.nom, "sigle": institution.sigle, "ville": institution.ville, "pays": institution.pays}})


@csrf_exempt
@require_POST
def enregistrer_institution(requete):
    try:
        donnees = lire_json(requete)
        institution, _ = Institution.objects.get_or_create(pk=1)
        institution.nom = donnees["nom"].strip()
        institution.sigle = donnees["sigle"].strip()
        institution.ville = donnees.get("ville", "").strip()
        institution.pays = donnees.get("pays", "Mali").strip()
        institution.save()
    except (KeyError, TypeError, ValueError) as erreur:
        return JsonResponse({"erreur": f"Données invalides : {erreur}"}, status=400)
    return JsonResponse({"institution": {"nom": institution.nom, "sigle": institution.sigle, "ville": institution.ville, "pays": institution.pays}})


@csrf_exempt
@require_POST
def analyser_demande_credit(requete):
    try:
        donnees = lire_json(requete)
        identifiant_client = donnees.get("identifiant_client")
        if identifiant_client:
            client = Client.objects.get(pk=int(identifiant_client))
        else:
            client = Client.objects.create(
                nom_complet=donnees["nom_complet"],
                secteur_activite=donnees["secteur_activite"],
                revenu_mensuel=int(donnees["revenu_mensuel"]),
                charges_mensuelles=int(donnees["charges_mensuelles"]),
                mensualite_dette_existante=int(donnees.get("mensualite_dette_existante", 0)),
                anciennete_activite_mois=int(donnees["anciennete_activite_mois"]),
                nombre_retards=int(donnees.get("nombre_retards", 0)),
                regularite_tontine=donnees.get("regularite_tontine", "inconnue"),
            )
        demande_credit = DemandeCredit.objects.create(client=client, montant_demande=int(donnees["montant_demande"]), duree_mois=int(donnees.get("duree_mois", 12)))
    except (Client.DoesNotExist, KeyError, TypeError, ValueError) as erreur:
        return JsonResponse({"erreur": f"Donnees invalides : {erreur}"}, status=400)

    prediction = predire_risque(client, demande_credit)
    demande_credit.score_risque = prediction["score_risque"]
    demande_credit.niveau_risque = prediction["niveau_risque"]
    demande_credit.save(update_fields=["score_risque", "niveau_risque"])
    explication = expliquer_prediction(prediction)
    JournalAudit.objects.create(demande_credit=demande_credit, type_evenement="ANALYSE_RISQUE_EFFECTUEE", contenu={"prediction": prediction, "explication": explication})
    return JsonResponse({"identifiant_demande": demande_credit.id, "identifiant_client": client.id, "score_risque": prediction["score_risque"], "niveau_risque": prediction["niveau_risque"], "recommandation": prediction["recommandation"], "indicateurs": prediction["caracteristiques"], "explication": explication}, status=201)
