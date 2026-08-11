def explain(prediction):
    return {
        "positive_factors": prediction["positive_factors"],
        "warnings": prediction["warnings"],
        "triggered_rules": prediction["triggered_rules"],
        "message": "Score indicatif fonde sur des regles explicites, pas sur une decision automatique.",
    }
