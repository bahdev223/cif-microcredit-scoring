import json

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from audit.models import AuditLog
from clients.models import Client
from credits.models import CreditApplication
from scoring.explainability import explain
from scoring.predictor import predict


@require_GET
def health(request):
    return JsonResponse({"status": "ok", "service": "cif-microcredit-scoring"})


@require_POST
def analyze_credit(request):
    try:
        data = json.loads(request.body)
        client = Client.objects.create(
            full_name=data["full_name"],
            sector=data["sector"],
            monthly_income=int(data["monthly_income"]),
            monthly_expenses=int(data["monthly_expenses"]),
            business_age_months=int(data["business_age_months"]),
            late_payments=int(data.get("late_payments", 0)),
            tontine_regularity=data.get("tontine_regularity", "unknown"),
        )
        application = CreditApplication.objects.create(client=client, amount=int(data["amount"]), term_months=int(data.get("term_months", 12)))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        return JsonResponse({"error": f"Donnees invalides : {error}"}, status=400)

    prediction = predict(client, application)
    application.risk_score = prediction["score"]
    application.risk_level = prediction["risk_level"]
    application.save(update_fields=["risk_score", "risk_level"])
    explanation = explain(prediction)
    AuditLog.objects.create(application=application, event_type="SCORING_ANALYZED", payload={"prediction": prediction, "explanation": explanation})
    return JsonResponse({"application_id": application.id, "client_id": client.id, "score": prediction["score"], "risk_level": prediction["risk_level"], "recommendation": prediction["recommendation"], "explanation": explanation}, status=201)
