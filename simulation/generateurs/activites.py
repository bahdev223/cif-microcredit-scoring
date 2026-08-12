"""Génération des historiques mensuels d'activité économique."""

from datetime import date


def mois_entre(date_debut, date_fin):
    courant = date(date_debut.year, date_debut.month, 1)
    while courant <= date_fin:
        yield courant
        courant = date(courant.year + (courant.month == 12), 1 if courant.month == 12 else courant.month + 1, 1)


def coefficient_saisonnier(secteur, mois):
    if secteur == "Agriculture":
        return 0.65 if mois.month in (3, 4, 5, 6) else 1.35 if mois.month in (10, 11, 12) else 1.0
    if secteur == "Commerce":
        return 1.2 if mois.month in (11, 12) else 1.0
    return 1.0


def generer_activites(clients, profils_internes, date_debut, date_fin, aleatoire):
    lignes, resumes = [], {}
    for client in clients:
        identifiant_client = client["identifiant_client"]
        profil = profils_internes[identifiant_client]
        chiffre_affaires_base = aleatoire.randint(180_000, 1_400_000)
        marge_base = aleatoire.uniform(0.10, 0.38)
        valeurs = []
        for numero_mois, mois in enumerate(mois_entre(date_debut, date_fin), 1):
            saisonnalite = coefficient_saisonnier(client["secteur_activite"], mois)
            bruit = aleatoire.uniform(0.78, 1.22) * profil["stabilite_activite"]
            chiffre_affaires = max(50_000, round(chiffre_affaires_base * saisonnalite * bruit))
            charges = round(chiffre_affaires * (1 - marge_base + aleatoire.uniform(-0.06, 0.06)))
            ligne = {
                "identifiant_activite": f"ACT-{identifiant_client[4:]}-{numero_mois:03d}",
                "identifiant_client": identifiant_client,
                "mois": mois.isoformat(),
                "chiffre_affaires": chiffre_affaires,
                "charges_activite": max(0, charges),
                "saisonnalite": round(saisonnalite, 2),
            }
            lignes.append(ligne)
            valeurs.append(ligne)
        derniers = valeurs[-6:]
        resumes[identifiant_client] = {
            "marge_mensuelle": round(sum(v["chiffre_affaires"] - v["charges_activite"] for v in derniers) / len(derniers)),
            "variabilite": round(max(v["chiffre_affaires"] for v in derniers) / max(1, min(v["chiffre_affaires"] for v in derniers)), 2),
        }
    return lignes, resumes
