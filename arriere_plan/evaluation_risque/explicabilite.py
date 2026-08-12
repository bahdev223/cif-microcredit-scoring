def expliquer_prediction(prediction):
    return {
        "facteurs_favorables": prediction["facteurs_favorables"],
        "points_vigilance": prediction["points_vigilance"],
        "regles_declenchees": prediction["regles_declenchees"],
        "message": "Score indicatif fonde sur des regles explicites, pas sur une decision automatique.",
    }
