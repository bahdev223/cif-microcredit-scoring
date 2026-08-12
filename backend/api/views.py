import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from audit.models import JournalAudit
from clients.models import Client, Institution
from credits.models import DemandeCredit
from evaluation_risque.explicabilite import expliquer_prediction
from evaluation_risque.predicteur import predire_risque


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
