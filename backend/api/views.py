import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from audit.models import JournalAudit
from clients.models import Client
from credits.models import DemandeCredit
from evaluation_risque.explicabilite import expliquer_prediction
from evaluation_risque.predicteur import predire_risque


@require_GET
def etat_service(requete):
    return JsonResponse({"etat": "operationnel", "service": "evaluation-microcredit-cif"})


@csrf_exempt
@require_POST
def analyser_demande_credit(requete):
    try:
        donnees = json.loads(requete.body)
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
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as erreur:
        return JsonResponse({"erreur": f"Donnees invalides : {erreur}"}, status=400)

    prediction = predire_risque(client, demande_credit)
    demande_credit.score_risque = prediction["score_risque"]
    demande_credit.niveau_risque = prediction["niveau_risque"]
    demande_credit.save(update_fields=["score_risque", "niveau_risque"])
    explication = expliquer_prediction(prediction)
    JournalAudit.objects.create(demande_credit=demande_credit, type_evenement="ANALYSE_RISQUE_EFFECTUEE", contenu={"prediction": prediction, "explication": explication})
    return JsonResponse({"identifiant_demande": demande_credit.id, "identifiant_client": client.id, "score_risque": prediction["score_risque"], "niveau_risque": prediction["niveau_risque"], "recommandation": prediction["recommandation"], "indicateurs": prediction["caracteristiques"], "explication": explication}, status=201)
