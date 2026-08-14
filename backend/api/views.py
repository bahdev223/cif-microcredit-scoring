import json
import csv
from io import StringIO
from pathlib import Path

from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from django.conf import settings

from acquisition.qualite import evaluer as evaluer_qualite
from audit.models import JournalAudit
from clients.dossier import construire_dossier
from clients.models import ActiviteImportee, Client, DocumentDossier, Institution
from cadres.models import CadreAnalyse
from credits.models import CreditImporte, DemandeCredit, DemandeImportee, EcheanceImportee, PaiementImporte, ProduitCredit
from credits.rapprochement import date_observation_portefeuille, rapprocher_credit, tranche_retard
from analyse.dossier import analyser as analyser_coeur

FICHIERS_IMPORT = {
    "clients.csv": {"identifiant_client", "identifiant_institution", "code_secteur_principal", "anciennete_activite_mois_a_entree"},
    "activites.csv": {"identifiant_activite", "identifiant_client", "identifiant_institution"},
    "demandes_credit.csv": {"identifiant_demande", "identifiant_client", "identifiant_institution", "montant_demande", "duree_demandee_mois"},
    "credits.csv": {"identifiant_credit", "identifiant_demande", "identifiant_institution"},
    "echeances.csv": {"identifiant_echeance", "identifiant_credit", "identifiant_institution"},
    "paiements.csv": {"identifiant_paiement", "identifiant_credit", "identifiant_echeance", "identifiant_institution"},
}

RACINE_PROJET = Path(__file__).resolve().parents[2]
REPERTOIRE_LOTS = RACINE_PROJET / "donnees" / "synthetiques"


@require_GET
def liste_lots_import(requete):
    lots = []
    for dossier in sorted(REPERTOIRE_LOTS.glob("institution_*")):
        fichiers = {chemin.name for chemin in dossier.glob("*.csv")}
        if set(FICHIERS_IMPORT).issubset(fichiers):
            lots.append({"code": dossier.name, "libelle": dossier.name.replace("_", " ").title()})
    return JsonResponse({"lots": lots, "fichiers_attendus": sorted(FICHIERS_IMPORT)})


@require_GET
def tableau_bord(requete):
    """Indicateurs de risque du portefeuille, calculés sur les données réelles.

    Aucun agenda d'encaissement n'est produit : les échéances à venir sont le
    travail du système de l'institution. Ce qui est compté ici, ce sont les
    retards constatés, parce qu'ils portent le comportement observé.

    Aucun indicateur réglementaire (PAR30, créances douteuses, provisionnement)
    n'est produit ici : ces définitions appartiennent à l'institution et seront
    ajoutées après validation métier.
    """
    date_observation = date_observation_portefeuille()
    credits = list(CreditImporte.objects.select_related("client").prefetch_related("echeances", "paiements"))
    rapprochements = [rapprocher_credit(credit, date_observation) for credit in credits]

    encours = sum(r["reste_du"] for r in rapprochements)
    credits_actifs = [r for r in rapprochements if r["statut"] in ("EN_COURS", "EN_RETARD")]
    credits_en_retard = [r for r in rapprochements if r["statut"] == "EN_RETARD"]
    clients_avec_credit_actif = {
        credit.client_id
        for credit, rapprochement in zip(credits, rapprochements)
        if rapprochement["statut"] in ("EN_COURS", "EN_RETARD")
    }

    tranches = {}
    montant_en_retard = 0
    for rapprochement in rapprochements:
        for echeance in rapprochement["echeances"]:
            if echeance["en_retard"]:
                montant_en_retard += echeance["reste_du"]
                libelle = tranche_retard(echeance["jours_retard"])
                tranches[libelle] = tranches.get(libelle, 0) + 1

    demandes = DemandeCredit.objects.select_related("client").order_by("-cree_le")
    a_instruire = [demande for demande in demandes if demande.decision_agent == "EN_ATTENTE"]

    return JsonResponse({
        "date_observation": date_observation.isoformat(),
        "clients": Client.objects.count(),
        "clients_avec_credit_actif": len(clients_avec_credit_actif),
        "demandes_en_cours": len(a_instruire),
        "credits": len(rapprochements),
        "credits_actifs": len(credits_actifs),
        "credits_en_retard": len(credits_en_retard),
        "montant_decaisse": sum(r["montant_decaisse"] for r in rapprochements),
        "montant_rembourse": sum(r["total_paye"] for r in rapprochements),
        "encours": encours,
        "echeances_en_retard": sum(r["nombre_echeances_en_retard"] for r in rapprochements),
        "montant_en_retard": montant_en_retard,
        "tranches_retard": [{"libelle": libelle, "nombre": nombre} for libelle, nombre in sorted(tranches.items())],
        "demandes_attention": [{
            "identifiant": demande.id,
            "identifiant_client": demande.client_id,
            "client": demande.client.nom_complet,
            "montant_demande": demande.montant_demande,
            "duree_mois": demande.duree_mois,
            "etat": "En attente de décision",
        } for demande in a_instruire[:8]],
    })


def lire_csv_importe(fichier):
    texte = fichier.read().decode("utf-8-sig")
    lecteur = csv.DictReader(StringIO(texte))
    if not lecteur.fieldnames:
        raise ValueError(f"{fichier.name} ne contient pas d'en-têtes.")
    lignes = list(lecteur)
    manquantes = sorted(FICHIERS_IMPORT[fichier.name] - set(lecteur.fieldnames))
    return lignes, manquantes


def analyser_lot_import(requete):
    """Lit les fichiers déposés puis produit le rapport qualité par dimension."""
    fichiers = {fichier.name: fichier for fichier in requete.FILES.getlist("fichiers")}
    tables, erreurs_lecture = {}, []

    for nom in FICHIERS_IMPORT:
        if nom not in fichiers:
            erreurs_lecture.append(f"{nom} est manquant.")
            continue
        try:
            lignes, manquantes = lire_csv_importe(fichiers[nom])
            tables[nom.replace(".csv", "")] = lignes
            if manquantes:
                erreurs_lecture.append(f"{nom} : colonnes manquantes — {', '.join(manquantes)}.")
            if not lignes:
                erreurs_lecture.append(f"{nom} ne contient aucune ligne.")
        except (UnicodeDecodeError, ValueError) as erreur:
            erreurs_lecture.append(str(erreur))

    champs_attendus = {
        nom.replace(".csv", ""): sorted(champs)
        for nom, champs in FICHIERS_IMPORT.items()
    }
    rapport = evaluer_qualite(tables, champs_attendus)
    rapport["erreurs"] = erreurs_lecture + rapport["erreurs"]
    rapport["integrable"] = not rapport["erreurs"]
    rapport["lignes"] = {nom: len(lignes) for nom, lignes in tables.items()}
    return {nom + ".csv": lignes for nom, lignes in tables.items()}, rapport


@csrf_exempt
@require_POST
def valider_import_csv(requete):
    try:
        _, rapport = analyser_lot_import(requete)
    except Exception as erreur:
        return JsonResponse({"erreur": f"Lecture impossible : {erreur}"}, status=400)
    return JsonResponse(rapport)


@csrf_exempt
@require_POST
def confirmer_import_csv(requete):
    try:
        tables, rapport = analyser_lot_import(requete)
    except Exception as erreur:
        return JsonResponse({"erreur": f"Lecture impossible : {erreur}"}, status=400)
    if not rapport["integrable"]:
        return JsonResponse({"erreur": "Le lot contient des erreurs bloquantes et ne peut pas être importé.",
                             "erreurs": rapport["erreurs"]}, status=400)

    clients_par_source = {}
    ajoutes = 0
    for ligne in tables["clients.csv"]:
        client, cree = Client.objects.update_or_create(
            identifiant_source=ligne["identifiant_client"],
            defaults={
                "nom_complet": nom_fictif(ligne["identifiant_client"]),
                "identifiant_institution_source": ligne.get("identifiant_institution", ""),
                "secteur_activite": ligne.get("code_secteur_principal", "Non renseigné").replace("_", " ").title(),
                "anciennete_activite_mois": int(ligne.get("anciennete_activite_mois_a_entree") or 0),
            },
        )
        clients_par_source[ligne["identifiant_client"]] = client
        ajoutes += int(cree)

    for ligne in tables["activites.csv"]:
        client = clients_par_source.get(ligne.get("identifiant_client"))
        if client:
            ActiviteImportee.objects.update_or_create(
                identifiant_source=ligne["identifiant_activite"],
                defaults={"client": client, "secteur": ligne.get("code_secteur", ""),
                          "libelle": ligne.get("libelle_activite", ""),
                          "est_principale": ligne.get("est_activite_principale") == "1",
                          "date_debut": ligne.get("date_debut_activite") or None},
            )
    demandes = {ligne["identifiant_demande"]: ligne for ligne in tables["demandes_credit.csv"]}
    for ligne in demandes.values():
        client = clients_par_source.get(ligne.get("identifiant_client"))
        if client:
            DemandeImportee.objects.update_or_create(
                identifiant_source=ligne["identifiant_demande"],
                defaults={"client": client, "montant": int(ligne.get("montant_demande") or 0),
                          "duree_mois": int(ligne.get("duree_demandee_mois") or 0),
                          "date_demande": ligne.get("date_demande") or None,
                          "objet": ligne.get("objet_credit", "")},
            )
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
    return JsonResponse({"message": "Import confirmé.", "clients_ajoutes": ajoutes, "credits_importes": len(credits_par_source),
                         "demandes_importees": len(demandes), "activites_importees": len(tables["activites.csv"]),
                         "avertissements": rapport["avertissements"], "total_lignes": rapport["total_lignes"]})


@require_GET
def detail_client(requete, identifiant_client):
    try:
        client = Client.objects.get(pk=identifiant_client)
    except Client.DoesNotExist:
        return JsonResponse({"erreur": "Client introuvable."}, status=404)
    date_observation = date_observation_portefeuille()
    dossier = construire_dossier(client, date_observation)
    dossier["date_observation"] = date_observation.isoformat()
    dossier["client"].update(serialiser_client(client))
    return JsonResponse(dossier)


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
        "identifiant_source": client.identifiant_source or "",
        "nom_complet": client.nom_complet,
        "secteur_activite": client.secteur_activite,
        "anciennete_activite_mois": client.anciennete_activite_mois,
        "cree_le": client.cree_le.isoformat(),
    }


@csrf_exempt
@require_GET
def liste_clients(requete):
    recherche = requete.GET.get("recherche", "").strip()
    clients = Client.objects.order_by("-cree_le")
    if recherche:
        clients = clients.filter(nom_complet__icontains=recherche)
    page = Paginator(clients, int(requete.GET.get("taille", 20))).get_page(requete.GET.get("page", 1))
    return JsonResponse({"resultats": [serialiser_client(client) for client in page],
                         "pagination": {"page": page.number, "pages": page.paginator.num_pages, "total": page.paginator.count}})


LIBELLES_AUDIT = {
    "ANALYSE_PRELIMINAIRE_EFFECTUEE": "Analyse préliminaire effectuée",
    "ANALYSE_RISQUE_EFFECTUEE": "Analyse préliminaire effectuée",
    "SIMULATION_APPLIQUEE": "Simulation appliquée au dossier",
    "DECISION_ENREGISTREE": "Décision enregistrée",
}


def resumer_evenement_audit(journal):
    """Phrase lisible décrivant ce qui s'est passé, à partir du contenu tracé."""
    contenu = journal.contenu or {}
    if journal.type_evenement == "SIMULATION_APPLIQUEE":
        avant, apres = contenu.get("avant", {}), contenu.get("apres", {})
        return (f"{avant.get('montant', '?')} F sur {avant.get('duree_mois', '?')} mois "
                f"→ {apres.get('montant', '?')} F sur {apres.get('duree_mois', '?')} mois")
    if journal.type_evenement == "DECISION_ENREGISTREE":
        motif = contenu.get("motif") or "sans motif renseigné"
        return f"{contenu.get('decision', '')} — {motif}"
    return ""


@require_GET
def liste_audit(requete):
    page = Paginator(JournalAudit.objects.select_related("demande_credit__client").order_by("-cree_le"), int(requete.GET.get("taille", 30))).get_page(requete.GET.get("page", 1))
    return JsonResponse({"resultats": [{
        "evenement": LIBELLES_AUDIT.get(journal.type_evenement, journal.type_evenement),
        "code_evenement": journal.type_evenement,
        "client": journal.demande_credit.client.nom_complet,
        "identifiant_client": journal.demande_credit.client_id,
        "reference_demande": f"DEM-{journal.demande_credit_id:05d}",
        "detail": resumer_evenement_audit(journal),
        "date": journal.cree_le.isoformat(),
    } for journal in page],
        "pagination": {"page": page.number, "pages": page.paginator.num_pages, "total": page.paginator.count}})


@csrf_exempt
@require_POST
def creer_client(requete):
    try:
        donnees = lire_json(requete)
        client = Client.objects.create(
            nom_complet=donnees["nom_complet"].strip(),
            secteur_activite=donnees["secteur_activite"].strip(),
            anciennete_activite_mois=int(donnees["anciennete_activite_mois"]),
        )
    except (KeyError, TypeError, ValueError) as erreur:
        return JsonResponse({"erreur": f"Données invalides : {erreur}"}, status=400)
    return JsonResponse({"client": serialiser_client(client)}, status=201)


@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def modifier_client(requete, identifiant_client):
    try:
        donnees = lire_json(requete)
        client = Client.objects.get(pk=identifiant_client)
        champs = (
            "nom_complet", "secteur_activite", "anciennete_activite_mois",
        )
        for champ in champs:
            if champ in donnees:
                valeur = donnees[champ]
                setattr(client, champ, valeur.strip() if champ in ("nom_complet", "secteur_activite") else valeur)
        client.full_clean()
        client.save()
    except Client.DoesNotExist:
        return JsonResponse({"erreur": "Client introuvable."}, status=404)
    except (TypeError, ValueError) as erreur:
        return JsonResponse({"erreur": f"Données invalides : {erreur}"}, status=400)
    return JsonResponse({"client": serialiser_client(client)})


@csrf_exempt
@require_http_methods(["DELETE"])
def supprimer_client(requete, identifiant_client):
    try:
        client = Client.objects.get(pk=identifiant_client)
        nom = client.nom_complet
        client.delete()
    except Client.DoesNotExist:
        return JsonResponse({"erreur": "Client introuvable."}, status=404)
    except Exception:
        return JsonResponse({"erreur": "Ce client possède des demandes métier protégées. Supprimez ou archivez d'abord ses demandes."}, status=409)
    return JsonResponse({"message": f"Client « {nom} » supprimé."})


@csrf_exempt
@require_GET
def liste_demandes_credit(requete):
    demandes = DemandeCredit.objects.select_related("client").order_by("-cree_le")[:100]
    return JsonResponse({"demandes": [{
        "identifiant": demande.id,
        "identifiant_client": demande.client_id,
        "client": demande.client.nom_complet,
        "montant_demande": demande.montant_demande,
        "duree_mois": demande.duree_mois,
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


def serialiser_document(document):
    return {
        "identifiant": document.id,
        "categorie": document.categorie,
        "libelle_categorie": document.get_categorie_display(),
        "nom_original": document.nom_original,
        "taille_octets": document.taille_octets,
        "url": document.fichier.url,
        "televerse_le": document.televerse_le.isoformat(),
    }


@require_GET
def liste_documents_client(requete, identifiant_client):
    """Documents joints, et pièces attendues encore absentes."""
    try:
        client = Client.objects.get(pk=identifiant_client)
    except Client.DoesNotExist:
        return JsonResponse({"erreur": "Client introuvable."}, status=404)

    documents = list(client.documents.order_by("-televerse_le"))
    presentes = {document.categorie for document in documents}
    return JsonResponse({
        "documents": [serialiser_document(document) for document in documents],
        "categories": [
            {"code": code, "libelle": libelle, "present": code in presentes}
            for code, libelle in DocumentDossier.CATEGORIES
        ],
    })


@csrf_exempt
@require_POST
def televerser_document(requete, identifiant_client):
    try:
        client = Client.objects.get(pk=identifiant_client)
    except Client.DoesNotExist:
        return JsonResponse({"erreur": "Client introuvable."}, status=404)

    fichier = requete.FILES.get("fichier")
    categorie = requete.POST.get("categorie", "")
    if not fichier:
        return JsonResponse({"erreur": "Aucun fichier reçu."}, status=400)
    if categorie not in {code for code, _ in DocumentDossier.CATEGORIES}:
        return JsonResponse({"erreur": "Catégorie de document inconnue."}, status=400)

    extension = Path(fichier.name).suffix.lower()
    if extension not in settings.EXTENSIONS_DOCUMENTS_AUTORISEES:
        autorisees = ", ".join(sorted(settings.EXTENSIONS_DOCUMENTS_AUTORISEES))
        return JsonResponse({"erreur": f"Format non accepté. Formats autorisés : {autorisees}."}, status=400)
    if fichier.size > settings.TAILLE_MAXIMALE_DOCUMENT:
        limite = settings.TAILLE_MAXIMALE_DOCUMENT // (1024 * 1024)
        return JsonResponse({"erreur": f"Fichier trop volumineux : {limite} Mo maximum."}, status=400)

    document = DocumentDossier.objects.create(
        client=client,
        categorie=categorie,
        fichier=fichier,
        nom_original=fichier.name[:200],
        taille_octets=fichier.size,
    )
    return JsonResponse({"document": serialiser_document(document)}, status=201)


@csrf_exempt
@require_http_methods(["DELETE"])
def supprimer_document(requete, identifiant_document):
    try:
        document = DocumentDossier.objects.get(pk=identifiant_document)
    except DocumentDossier.DoesNotExist:
        return JsonResponse({"erreur": "Document introuvable."}, status=404)
    document.fichier.delete(save=False)
    document.delete()
    return JsonResponse({"message": "Document supprimé."})


@require_GET
def vue_portefeuille(requete):
    """Portefeuille filtrable, avec des indicateurs strictement descriptifs.

    Les filtres proposés sont ceux que les données permettent réellement.
    L'agence et le produit ne sont pas encore portés par les crédits importés :
    ils sont annoncés comme indisponibles plutôt que proposés à vide.
    """
    date_observation = date_observation_portefeuille()
    secteur = requete.GET.get("secteur", "")
    statut_demande = requete.GET.get("statut", "")
    annee = requete.GET.get("annee", "")

    credits = CreditImporte.objects.select_related("client").prefetch_related("echeances", "paiements")
    if secteur:
        credits = credits.filter(client__secteur_activite=secteur)
    if annee:
        credits = credits.filter(date_decaissement__year=annee)

    lignes = []
    for credit in credits:
        rapprochement = rapprocher_credit(credit, date_observation)
        if statut_demande and rapprochement["statut"] != statut_demande:
            continue
        rapprochement["client"] = credit.client.nom_complet
        rapprochement["identifiant_client"] = credit.client_id
        rapprochement["secteur"] = credit.client.secteur_activite
        lignes.append(rapprochement)

    lignes.sort(key=lambda ligne: ligne["date_decaissement"], reverse=True)
    repartition_secteur = {}
    for ligne in lignes:
        entree = repartition_secteur.setdefault(ligne["secteur"], {"nombre": 0, "encours": 0})
        entree["nombre"] += 1
        entree["encours"] += ligne["reste_du"]

    return JsonResponse({
        "date_observation": date_observation.isoformat(),
        "indicateurs": {
            "credits": len(lignes),
            "credits_actifs": sum(1 for l in lignes if l["statut"] in ("EN_COURS", "EN_RETARD")),
            "montant_decaisse": sum(l["montant_decaisse"] for l in lignes),
            "encours": sum(l["reste_du"] for l in lignes),
            "montant_rembourse": sum(l["total_paye"] for l in lignes),
            "credits_en_retard": sum(1 for l in lignes if l["statut"] == "EN_RETARD"),
        },
        "repartition_secteur": [
            {"libelle": libelle, **valeurs}
            for libelle, valeurs in sorted(repartition_secteur.items(), key=lambda couple: -couple[1]["nombre"])
        ],
        "credits": [{
            "identifiant": ligne["identifiant"],
            "identifiant_client": ligne["identifiant_client"],
            "client": ligne["client"],
            "secteur": ligne["secteur"],
            "montant_decaisse": ligne["montant_decaisse"],
            "reste_du": ligne["reste_du"],
            "date_decaissement": ligne["date_decaissement"],
            "duree_mois": ligne["duree_mois"],
            "statut": ligne["statut"],
            "jours_retard_max": ligne["jours_retard_max"],
        } for ligne in lignes[:200]],
        "filtres": {
            "secteurs": sorted({valeur for valeur in Client.objects.values_list("secteur_activite", flat=True) if valeur}),
            "annees": sorted({date.year for date in CreditImporte.objects.values_list("date_decaissement", flat=True) if date}, reverse=True),
            "statuts": ["EN_COURS", "EN_RETARD", "SOLDE", "SOLDE_AVEC_RETARD", "SANS_ECHEANCIER"],
            "indisponibles": ["Agence", "Produit de crédit"],
        },
    })


@require_GET
def vue_retards(requete):
    """Échéances échues et non soldées, de la plus ancienne à la plus récente."""
    date_observation = date_observation_portefeuille()
    credits = CreditImporte.objects.select_related("client").prefetch_related("echeances", "paiements")

    impayes = []
    for credit in credits:
        rapprochement = rapprocher_credit(credit, date_observation)
        for echeance in rapprochement["echeances"]:
            if echeance["en_retard"]:
                impayes.append({
                    "identifiant_credit": rapprochement["identifiant"],
                    "identifiant_client": credit.client_id,
                    "client": credit.client.nom_complet,
                    "numero_echeance": echeance["numero"],
                    "date_exigible": echeance["date_exigible"],
                    "montant_du": echeance["montant_du"],
                    "montant_couvert": echeance["montant_couvert"],
                    "reste_du": echeance["reste_du"],
                    "jours_retard": echeance["jours_retard"],
                    "tranche": tranche_retard(echeance["jours_retard"]),
                })

    impayes.sort(key=lambda ligne: -ligne["jours_retard"])
    tranches = {}
    for impaye in impayes:
        entree = tranches.setdefault(impaye["tranche"], {"nombre": 0, "montant": 0})
        entree["nombre"] += 1
        entree["montant"] += impaye["reste_du"]

    return JsonResponse({
        "date_observation": date_observation.isoformat(),
        "indicateurs": {
            "echeances_en_retard": len(impayes),
            "montant_en_retard": sum(ligne["reste_du"] for ligne in impayes),
            "clients_concernes": len({ligne["identifiant_client"] for ligne in impayes}),
            "credits_concernes": len({ligne["identifiant_credit"] for ligne in impayes}),
        },
        "tranches": [{"libelle": libelle, **valeurs} for libelle, valeurs in sorted(tranches.items())],
        "impayes": impayes[:200],
    })


@csrf_exempt
@require_http_methods(["POST", "PUT", "DELETE"])
def gerer_produit_credit(requete, identifiant_produit=None):
    if requete.method == "DELETE":
        try:
            ProduitCredit.objects.get(pk=identifiant_produit).delete()
        except ProduitCredit.DoesNotExist:
            return JsonResponse({"erreur": "Produit introuvable."}, status=404)
        return JsonResponse({"message": "Produit supprimé."})

    try:
        donnees = lire_json(requete)
        champs = {
            "code": donnees["code"].strip().upper(),
            "libelle": donnees["libelle"].strip(),
            "montant_min": int(donnees.get("montant_min") or 0),
            "montant_max": int(donnees.get("montant_max") or 0),
            "duree_min_mois": int(donnees.get("duree_min_mois") or 0),
            "duree_max_mois": int(donnees.get("duree_max_mois") or 0),
            "secteurs_vises": (donnees.get("secteurs_vises") or "").strip(),
            "cadre_analyse_id": donnees.get("identifiant_cadre") or None,
        }
        if champs["montant_max"] and champs["montant_max"] < champs["montant_min"]:
            return JsonResponse({"erreur": "Le montant maximum est inférieur au montant minimum."}, status=400)
        if champs["duree_max_mois"] and champs["duree_max_mois"] < champs["duree_min_mois"]:
            return JsonResponse({"erreur": "La durée maximale est inférieure à la durée minimale."}, status=400)

        if identifiant_produit:
            produit = ProduitCredit.objects.get(pk=identifiant_produit)
            for champ, valeur in champs.items():
                setattr(produit, champ, valeur)
            produit.save()
        else:
            produit = ProduitCredit.objects.create(**champs)
    except ProduitCredit.DoesNotExist:
        return JsonResponse({"erreur": "Produit introuvable."}, status=404)
    except (KeyError, TypeError, ValueError) as erreur:
        return JsonResponse({"erreur": f"Données invalides : {erreur}"}, status=400)
    except Exception:
        return JsonResponse({"erreur": "Ce code produit existe déjà."}, status=409)

    return JsonResponse({"produit": {"identifiant": produit.id, "code": produit.code, "libelle": produit.libelle}}, status=201)


@require_GET
def liste_produits_credit(requete):
    produits = ProduitCredit.objects.filter(actif=True).order_by("libelle")
    return JsonResponse({"produits": [{
        "identifiant": produit.id,
        "code": produit.code,
        "libelle": produit.libelle,
        "montant_min": produit.montant_min,
        "montant_max": produit.montant_max,
        "duree_min_mois": produit.duree_min_mois,
        "duree_max_mois": produit.duree_max_mois,
        "secteurs_vises": produit.secteurs_vises,
        "identifiant_cadre": produit.cadre_analyse_id,
        "cadre": produit.cadre_analyse.reference if produit.cadre_analyse_id else "",
    } for produit in produits]})


@require_GET
def liste_cadres_analyse(requete):
    """Cadres publiés, proposés au rattachement d'un produit de crédit."""
    cadres = CadreAnalyse.objects.filter(statut="PUBLIE").order_by("nom", "-version")
    return JsonResponse({"cadres": [{
        "identifiant": cadre.id,
        "code": cadre.code,
        "reference": cadre.reference,
        "version": cadre.version,
    } for cadre in cadres]})


@csrf_exempt
@require_POST
def analyser_demande_credit(requete):
    """Enregistre un dossier de demande et produit son analyse préliminaire."""
    try:
        donnees = lire_json(requete)
        identifiant_client = donnees.get("identifiant_client")
        if identifiant_client:
            client = Client.objects.get(pk=int(identifiant_client))
        else:
            client = Client.objects.create(
                nom_complet=donnees["nom_complet"],
                secteur_activite=donnees["secteur_activite"],
                anciennete_activite_mois=int(donnees.get("anciennete_activite_mois") or 0),
            )

        demande_credit = DemandeCredit.objects.create(
            client=client,
            produit_id=donnees.get("identifiant_produit") or None,
            montant_demande=int(donnees["montant_demande"]),
            duree_mois=int(donnees.get("duree_mois", 12)),
            objet_credit=(donnees.get("objet_credit") or "").strip(),
            recettes_activite=int(donnees.get("recettes_activite") or 0),
            charges_activite=int(donnees.get("charges_activite") or 0),
            autres_revenus_menage=int(donnees.get("autres_revenus_menage") or 0),
            charges_menage=int(donnees.get("charges_menage") or 0),
            mensualite_dette_existante=int(donnees.get("mensualite_dette_existante") or 0),
            anciennete_activite_mois=int(donnees.get("anciennete_activite_mois") or client.anciennete_activite_mois or 0),
            saisonnalite_activite=(donnees.get("saisonnalite_activite") or "").strip(),
            observations_agent=(donnees.get("observations_agent") or "").strip(),
        )
    except (Client.DoesNotExist, KeyError, TypeError, ValueError) as erreur:
        return JsonResponse({"erreur": f"Données invalides : {erreur}"}, status=400)

    tracer_analyse(demande_credit, "DOSSIER_ENREGISTRE")
    return JsonResponse({
        "identifiant_demande": demande_credit.id,
        "identifiant_client": client.id,
    }, status=201)


def tracer_analyse(demande_credit, evenement):
    """Trace l'événement au journal, sans produire d'indicateur composite.

    L'analyse n'est pas figée dans la demande : elle est recalculée à chaque
    consultation, à partir des moteurs et du cadre en vigueur. Ce qui est
    conservé ici, c'est l'événement et sa date.
    """
    JournalAudit.objects.create(demande_credit=demande_credit, type_evenement=evenement, contenu={})

@require_GET
def dossier_instruction(requete, identifiant_demande):
    """Tout ce qu'il faut pour instruire une demande, sur un seul écran."""
    try:
        demande = DemandeCredit.objects.select_related("client", "produit").get(pk=identifiant_demande)
    except DemandeCredit.DoesNotExist:
        return JsonResponse({"erreur": "Demande introuvable."}, status=404)

    date_observation = date_observation_portefeuille()
    return JsonResponse({
        "demande": serialiser_demande(demande),
        "client": serialiser_client(demande.client),
        "analyse": analyser_coeur(demande, date_observation),
        "journal": [{
            "evenement": journal.type_evenement,
            "date": journal.cree_le.isoformat(),
        } for journal in demande.journaux_audit.order_by("-cree_le")[:20]],
        "date_observation": date_observation.isoformat(),
    })


def serialiser_demande(demande):
    return {
        "identifiant": demande.id,
        "reference": f"DEM-{demande.id:05d}",
        "identifiant_client": demande.client_id,
        "client": demande.client.nom_complet,
        "produit": demande.produit.libelle if demande.produit else "",
        "montant_demande": demande.montant_demande,
        "duree_mois": demande.duree_mois,
        "objet_credit": demande.objet_credit,
        "echeance_estimee": demande.echeance_estimee,
        "recettes_activite": demande.recettes_activite,
        "charges_activite": demande.charges_activite,
        "autres_revenus_menage": demande.autres_revenus_menage,
        "charges_menage": demande.charges_menage,
        "mensualite_dette_existante": demande.mensualite_dette_existante,
        "anciennete_activite_mois": demande.anciennete_activite_mois,
        "saisonnalite_activite": demande.saisonnalite_activite,
        "observations_agent": demande.observations_agent,
        "decision_agent": demande.decision_agent,
        "motif_decision": demande.motif_decision,
        "date_decision": demande.date_decision.isoformat() if demande.date_decision else "",
        "cree_le": demande.cree_le.isoformat(),
    }


@require_GET
def simuler_demande(requete, identifiant_demande):
    """Recalcule l'échéance pour un autre montant ou une autre durée.

    La demande n'est pas modifiée : la simulation sert à discuter, pas à
    décider. C'est l'agent qui choisit ensuite de l'appliquer ou non.
    """
    try:
        demande = DemandeCredit.objects.select_related("client").get(pk=identifiant_demande)
        montant = int(requete.GET.get("montant", demande.montant_demande))
        duree = max(1, int(requete.GET.get("duree", demande.duree_mois)))
    except DemandeCredit.DoesNotExist:
        return JsonResponse({"erreur": "Demande introuvable."}, status=404)
    except (TypeError, ValueError) as erreur:
        return JsonResponse({"erreur": f"Paramètres invalides : {erreur}"}, status=400)

    marge = demande.marge_estimee
    echeance_simulee = round(montant / duree)
    return JsonResponse({
        "situation_actuelle": {
            "montant": demande.montant_demande,
            "duree_mois": demande.duree_mois,
            "echeance_estimee": demande.echeance_estimee,
            "marge_estimee": marge,
            "ecart": marge - demande.echeance_estimee,
        },
        "simulation": {
            "montant": montant,
            "duree_mois": duree,
            "echeance_estimee": echeance_simulee,
            "marge_estimee": marge,
            "ecart": marge - echeance_simulee,
        },
    })


@csrf_exempt
@require_POST
def appliquer_simulation(requete, identifiant_demande):
    try:
        demande = DemandeCredit.objects.get(pk=identifiant_demande)
        donnees = lire_json(requete)
        ancien_montant, ancienne_duree = demande.montant_demande, demande.duree_mois
        demande.montant_demande = int(donnees["montant"])
        demande.duree_mois = max(1, int(donnees["duree_mois"]))
        demande.save(update_fields=["montant_demande", "duree_mois"])
    except DemandeCredit.DoesNotExist:
        return JsonResponse({"erreur": "Demande introuvable."}, status=404)
    except (KeyError, TypeError, ValueError) as erreur:
        return JsonResponse({"erreur": f"Données invalides : {erreur}"}, status=400)

    JournalAudit.objects.create(
        demande_credit=demande,
        type_evenement="SIMULATION_APPLIQUEE",
        contenu={
            "avant": {"montant": ancien_montant, "duree_mois": ancienne_duree},
            "apres": {"montant": demande.montant_demande, "duree_mois": demande.duree_mois},
        },
    )
    tracer_analyse(demande, "SIMULATION_APPLIQUEE")
    return JsonResponse({"demande": serialiser_demande(demande)})


@csrf_exempt
@require_POST
def enregistrer_decision(requete, identifiant_demande):
    """La décision est prise par l'agent. L'application se contente de la tracer."""
    decisions_valides = {code for code, _ in DemandeCredit.DECISIONS}
    try:
        demande = DemandeCredit.objects.get(pk=identifiant_demande)
        donnees = lire_json(requete)
        decision = donnees["decision"]
        if decision not in decisions_valides:
            return JsonResponse({"erreur": f"Décision inconnue : {decision}"}, status=400)
        demande.decision_agent = decision
        demande.motif_decision = (donnees.get("motif") or "").strip()
        demande.observations_agent = (donnees.get("observations") or "").strip()
        demande.date_decision = timezone.now()
        demande.save(update_fields=["decision_agent", "motif_decision", "observations_agent", "date_decision"])
    except DemandeCredit.DoesNotExist:
        return JsonResponse({"erreur": "Demande introuvable."}, status=404)
    except (KeyError, TypeError, ValueError) as erreur:
        return JsonResponse({"erreur": f"Données invalides : {erreur}"}, status=400)

    JournalAudit.objects.create(
        demande_credit=demande,
        type_evenement="DECISION_ENREGISTREE",
        contenu={"decision": demande.decision_agent, "motif": demande.motif_decision},
    )
    return JsonResponse({"demande": serialiser_demande(demande)})
