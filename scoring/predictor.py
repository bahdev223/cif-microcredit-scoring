from .features import build_features
from .rules import evaluate_rules


def predict(client, application):
    features = build_features(client, application)
    result = evaluate_rules(features)
    score = result["score"]
    result["risk_level"] = "LOW" if score < 30 else "MODERATE" if score < 60 else "HIGH"
    result["recommendation"] = {
        "LOW": "A examiner favorablement par l'agent.",
        "MODERATE": "Demander une verification complementaire avant decision.",
        "HIGH": "A ne pas valider sans analyse humaine approfondie.",
    }[result["risk_level"]]
    result["features"] = features
    return result
