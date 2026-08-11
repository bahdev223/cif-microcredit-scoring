def evaluate_rules(features):
    score = 45
    positive, warnings, rules = [], [], []

    if features["capacity_ratio"] >= 2:
        score -= 18
        positive.append("Capacite mensuelle confortable par rapport a l'echeance.")
    elif features["capacity_ratio"] >= 1:
        score -= 5
        positive.append("Capacite mensuelle suffisante mais a surveiller.")
    else:
        score += 25
        warnings.append("Capacite mensuelle inferieure a l'echeance estimee.")
        rules.append("R01 - capacite de remboursement insuffisante")

    if features["business_age_months"] >= 24:
        score -= 10
        positive.append("Activite exercee depuis au moins 24 mois.")
    elif features["business_age_months"] < 12:
        score += 12
        warnings.append("Activite recente : recul limite sur les revenus.")
        rules.append("R02 - anciennete faible")

    if features["late_payments"] == 0:
        score -= 8
        positive.append("Aucun retard de paiement renseigne.")
    else:
        score += 12 if features["late_payments"] <= 2 else 25
        warnings.append("Retards precedents declares.")
        rules.append("R03 - historique de retard")

    if features["tontine_regularity"] == "good":
        score -= 7
        positive.append("Cotisations tontine regulieres.")
    elif features["tontine_regularity"] == "none":
        score += 4
        warnings.append("Information tontine indisponible.")

    return {"score": max(5, min(95, round(score))), "positive_factors": positive, "warnings": warnings, "triggered_rules": rules or ["Aucune regle bloquante declenchee"]}
