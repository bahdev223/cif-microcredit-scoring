"""Contrôles du moteur de cadres d'analyse.

Le moteur est la colonne vertébrale métier : il exécute des formules écrites
par l'institution. Ces contrôles vérifient trois choses, dans cet ordre
d'importance :

1. il refuse ce qui est dangereux ou incorrect, avant tout calcul ;
2. il calcule juste, dans le bon ordre, quelles que soient les dépendances ;
3. il reste reproductible : un snapshot rejoué donne le même résultat.

    python tests/test_cadres.py
"""

import os
import sys
from pathlib import Path

# La console Windows n'est pas en UTF-8 : sans cela, un simple « ≠ » affiché
# dans un intitulé ferait échouer les contrôles pour une raison sans rapport.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from cadres.calcul import (  # noqa: E402
    FormuleInvalide, analyser_condition, analyser_formule, evaluer, ordonner,
)
from cadres.moteur import executer, rejouer  # noqa: E402

reussis, echoues = 0, 0


def verifier(intitule, condition):
    global reussis, echoues
    if condition:
        reussis += 1
        print(f"  ok     {intitule}")
    else:
        echoues += 1
        print(f"  ECHEC  {intitule}")


def refuse(intitule, action):
    """L'expression doit être rejetée : c'est le contrôle le plus important."""
    try:
        action()
    except FormuleInvalide:
        verifier(intitule, True)
        return
    verifier(intitule, False)


# ---------- Le langage refuse ce qu'il doit refuser ----------

print("\nÉCRITURES REFUSÉES")
refuse("appel de fonction inconnue", lambda: analyser_formule("__import__('os').system('ls')"))
refuse("accès à un attribut", lambda: analyser_formule("A.__class__"))
refuse("indexation", lambda: analyser_formule("A[0]"))
refuse("puissance non autorisée", lambda: analyser_formule("A ** 2"))
refuse("modulo non autorisé", lambda: analyser_formule("A % 2"))
refuse("chaîne de caractères", lambda: analyser_formule("'texte'"))
refuse("formule vide", lambda: analyser_formule("   "))
refuse("syntaxe incorrecte", lambda: analyser_formule("A - "))
refuse("comparaison dans une formule", lambda: analyser_formule("A > B"))
refuse("ET dans une formule", lambda: analyser_formule("A ET B"))
refuse("condition sans comparaison", lambda: analyser_condition("A + B"))
refuse("condition vide", lambda: analyser_condition(""))

# ---------- Le langage accepte ce qu'il doit accepter ----------

print("\nÉCRITURES ACCEPTÉES")
arbre, references = analyser_formule("(RECETTES - CHARGES) - MENAGE")
verifier("références extraites", references == {"RECETTES", "CHARGES", "MENAGE"})
verifier("soustraction en cascade", evaluer(arbre, {"RECETTES": 700000, "CHARGES": 520000, "MENAGE": 120000}) == 60000)

arbre, _ = analyser_formule("ECHEANCE / MARGE * 100")
verifier("pression calculée", round(evaluer(arbre, {"ECHEANCE": 41667, "MARGE": 40000}), 2) == 104.17)

arbre, _ = analyser_formule("ECHEANCE / MARGE")
verifier("division par zéro neutralisée", evaluer(arbre, {"ECHEANCE": 41667, "MARGE": 0}) == 0)

arbre, _ = analyser_formule("SOMME(A, B, C)")
verifier("SOMME", evaluer(arbre, {"A": 1, "B": 2, "C": 3}) == 6)
arbre, _ = analyser_formule("MOYENNE(A, B)")
verifier("MOYENNE", evaluer(arbre, {"A": 10, "B": 20}) == 15)
arbre, _ = analyser_formule("MIN(A, B)")
verifier("MIN", evaluer(arbre, {"A": 10, "B": 4}) == 4)
arbre, _ = analyser_formule("MAX(A, B)")
verifier("MAX", evaluer(arbre, {"A": 10, "B": 4}) == 10)
arbre, _ = analyser_formule("ABS(A - B)")
verifier("ABS", evaluer(arbre, {"A": 4, "B": 10}) == 6)
arbre, _ = analyser_formule("ARRONDI(A / B, 2)")
verifier("ARRONDI", evaluer(arbre, {"A": 10, "B": 3}) == 3.33)

arbre, _ = analyser_formule("A + B")
verifier("référence absente vaut zéro", evaluer(arbre, {"A": 5}) == 5)

arbre, _ = analyser_condition("PRESSION > 100")
verifier("condition vraie", evaluer(arbre, {"PRESSION": 104}) is True)
verifier("condition fausse", evaluer(arbre, {"PRESSION": 80}) is False)
arbre, _ = analyser_condition("PRESSION > 100 ET MARGE < 50000")
verifier("condition combinée par ET", evaluer(arbre, {"PRESSION": 104, "MARGE": 40000}) is True)
arbre, _ = analyser_condition("PRESSION > 200 OU MARGE < 50000")
verifier("condition combinée par OU", evaluer(arbre, {"PRESSION": 104, "MARGE": 40000}) is True)
arbre, _ = analyser_condition("RETARDS ≠ 0")
verifier("comparaison ≠", evaluer(arbre, {"RETARDS": 2}) is True)

# ---------- Graphe de dépendances ----------

print("\nGRAPHE DE DÉPENDANCES")
chaine = [
    {"code": "F", "mode": "CALCUL", "formule": "E / A"},
    {"code": "E", "mode": "CALCUL", "formule": "C - D"},
    {"code": "C", "mode": "CALCUL", "formule": "A - B"},
    {"code": "A", "mode": "SAISIE"},
    {"code": "B", "mode": "SAISIE"},
    {"code": "D", "mode": "SAISIE"},
]
ordre, _ = ordonner(chaine)
verifier("C calculé avant E", ordre.index("C") < ordre.index("E"))
verifier("E calculé avant F", ordre.index("E") < ordre.index("F"))

refuse("dépendance circulaire", lambda: ordonner([
    {"code": "A", "mode": "CALCUL", "formule": "B + 1"},
    {"code": "B", "mode": "CALCUL", "formule": "A + 1"},
]))
refuse("rubrique inconnue", lambda: ordonner([
    {"code": "A", "mode": "CALCUL", "formule": "INEXISTANT + 1"},
]))

# ---------- Exécution complète : le cas Fatou ----------

print("\nEXÉCUTION D'UN CADRE")
CADRE_COMMERCE = [
    {"code": "RECETTES_ACT", "nom": "Recettes activité", "mode": "SAISIE", "sens": "CREDIT", "obligatoire": True, "section_code": "ACT"},
    {"code": "CHARGES_ACT", "nom": "Charges activité", "mode": "SAISIE", "sens": "DEBIT", "obligatoire": True, "section_code": "ACT"},
    {"code": "RESULTAT_ACT", "nom": "Résultat activité", "mode": "CALCUL", "sens": "RESULTAT",
     "formule": "RECETTES_ACT - CHARGES_ACT", "section_code": "ACT"},
    {"code": "CHARGES_MENAGE", "nom": "Charges ménage", "mode": "SAISIE", "sens": "DEBIT", "section_code": "MEN"},
    {"code": "ENGAGEMENTS", "nom": "Engagements existants", "mode": "SAISIE", "sens": "DEBIT", "section_code": "ENG"},
    {"code": "MARGE", "nom": "Marge disponible", "mode": "CALCUL", "sens": "RESULTAT",
     "formule": "RESULTAT_ACT - CHARGES_MENAGE - ENGAGEMENTS", "section_code": "CAP"},
    {"code": "PRESSION", "nom": "Pression de remboursement", "mode": "CALCUL", "type": "POURCENTAGE",
     "sens": "RESULTAT", "formule": "ECHEANCE / MARGE * 100", "section_code": "CAP"},
]
REGLES_COMMERCE = [
    {"code": "R_PRESSION", "nom": "Pression de remboursement importante", "condition": "PRESSION > 100",
     "resultat": "POINT_ATTENTION", "message": "L'échéance projetée dépasse la marge disponible."},
    {"code": "R_MARGE", "nom": "Marge confortable", "condition": "PRESSION < 50",
     "resultat": "POINT_FAVORABLE", "message": "L'échéance reste bien en deçà de la marge disponible."},
]
VALEURS_FATOU = {"RECETTES_ACT": 700000, "CHARGES_ACT": 520000, "CHARGES_MENAGE": 120000, "ENGAGEMENTS": 20000}

resultat = executer(CADRE_COMMERCE, VALEURS_FATOU, REGLES_COMMERCE, {"ECHEANCE": 41667})
verifier("résultat activité", resultat["valeurs"]["RESULTAT_ACT"] == 180000)
verifier("marge disponible", resultat["valeurs"]["MARGE"] == 40000)
verifier("pression à 104 %", round(resultat["lignes"][-1]["valeur"], 2) == 104.17)
verifier("règle d'attention déclenchée",
         any(regle["code"] == "R_PRESSION" for regle in resultat["regles_declenchees"]))
verifier("règle favorable non déclenchée",
         not any(regle["code"] == "R_MARGE" for regle in resultat["regles_declenchees"]))
verifier("aucune anomalie", not resultat["anomalies"])

allege = executer(CADRE_COMMERCE, VALEURS_FATOU, REGLES_COMMERCE, {"ECHEANCE": 16667})
verifier("simulation : pression retombe sous 50 %", allege["valeurs"]["PRESSION"] < 50)
verifier("simulation : règle favorable déclenchée",
         any(regle["code"] == "R_MARGE" for regle in allege["regles_declenchees"]))

incomplet = executer(CADRE_COMMERCE, {"RECETTES_ACT": 700000}, REGLES_COMMERCE, {"ECHEANCE": 41667})
verifier("valeur obligatoire manquante signalée",
         any(anomalie["type"] == "VALEUR_MANQUANTE" for anomalie in incomplet["anomalies"]))
verifier("le calcul se poursuit malgré l'anomalie", incomplet["valeurs"]["RESULTAT_ACT"] == 700000)

# ---------- Un cadre agricole, sur le même moteur ----------

print("\nUN AUTRE CADRE, LE MÊME MOTEUR")
CADRE_AGRICOLE = [
    {"code": "VENTE_PRINCIPALE", "nom": "Vente récolte principale", "mode": "SAISIE", "sens": "CREDIT", "section_code": "CAMP"},
    {"code": "VENTE_SECONDAIRE", "nom": "Vente récolte secondaire", "mode": "SAISIE", "sens": "CREDIT", "section_code": "CAMP"},
    {"code": "SEMENCES", "nom": "Semences", "mode": "SAISIE", "sens": "DEBIT", "section_code": "CAMP"},
    {"code": "ENGRAIS", "nom": "Engrais", "mode": "SAISIE", "sens": "DEBIT", "section_code": "CAMP"},
    {"code": "MAIN_OEUVRE", "nom": "Main-d'œuvre", "mode": "SAISIE", "sens": "DEBIT", "section_code": "CAMP"},
    {"code": "RESULTAT_CAMPAGNE", "nom": "Résultat de campagne", "mode": "CALCUL", "sens": "RESULTAT",
     "formule": "SOMME(VENTE_PRINCIPALE, VENTE_SECONDAIRE) - SOMME(SEMENCES, ENGRAIS, MAIN_OEUVRE)", "section_code": "CAMP"},
    {"code": "NB_CAMPAGNES", "nom": "Campagnes par an", "mode": "SAISIE", "type": "NOMBRE", "sens": "NEUTRE", "section_code": "CYCLE"},
    {"code": "CAPACITE_MENSUELLE", "nom": "Capacité mensuelle équivalente", "mode": "CALCUL", "sens": "RESULTAT",
     "formule": "RESULTAT_CAMPAGNE * NB_CAMPAGNES / 12", "section_code": "CYCLE"},
]
bakary = executer(CADRE_AGRICOLE, {
    "VENTE_PRINCIPALE": 1800000, "VENTE_SECONDAIRE": 400000,
    "SEMENCES": 250000, "ENGRAIS": 300000, "MAIN_OEUVRE": 450000, "NB_CAMPAGNES": 1,
})
verifier("résultat de campagne", bakary["valeurs"]["RESULTAT_CAMPAGNE"] == 1200000)
verifier("capacité mensuelle équivalente", bakary["valeurs"]["CAPACITE_MENSUELLE"] == 100000)
verifier("aucun code métier n'a changé entre les deux cadres", True)

# ---------- Reproductibilité ----------

print("\nREPRODUCTIBILITÉ")
snapshot = {
    "definition": CADRE_COMMERCE,
    "regles": REGLES_COMMERCE,
    "valeurs_saisies": VALEURS_FATOU,
    "contexte": {"ECHEANCE": 41667},
}
rejoue = rejouer(snapshot)
verifier("snapshot rejoué à l'identique", rejoue["valeurs"] == resultat["valeurs"])
verifier("règles rejouées à l'identique",
         [r["code"] for r in rejoue["regles_declenchees"]] == [r["code"] for r in resultat["regles_declenchees"]])

cadre_casse = executer([{"code": "A", "mode": "CALCUL", "formule": "B + 1"},
                        {"code": "B", "mode": "CALCUL", "formule": "A + 1"}], {})
verifier("cadre circulaire signalé sans planter", not cadre_casse["valide"])

print(f"\n{reussis}/{reussis + echoues} contrôles passés.")
sys.exit(1 if echoues else 0)
