"""Langage de formules des cadres d'analyse.

Les expressions sont écrites par l'institution, jamais par nous. Elles ne sont
donc jamais exécutées comme du code : `eval` n'apparaît nulle part. Chaque
expression est analysée en arbre, puis chaque nœud est vérifié contre une liste
blanche. Tout ce qui n'y figure pas — appel de fonction inconnue, attribut,
indexation, affectation, compréhension — est refusé à l'écriture, avant
d'atteindre la base.

Le langage autorise :

    opérateurs     + − × ÷ et parenthèses
    fonctions      SOMME MOYENNE MIN MAX ABS ARRONDI
    comparaisons   > < >= <= = ≠            (conditions de règles seulement)
    combinaisons   ET OU                    (conditions de règles seulement)

Une formule produit un nombre. Une condition produit un booléen. Les deux
grammaires sont volontairement séparées : on ne veut pas qu'une formule
retourne « vrai », ni qu'une règle additionne des montants.
"""

import ast

OPERATIONS = {
    ast.Add: lambda gauche, droite: gauche + droite,
    ast.Sub: lambda gauche, droite: gauche - droite,
    ast.Mult: lambda gauche, droite: gauche * droite,
    ast.Div: lambda gauche, droite: gauche / droite if droite else 0,
}

COMPARAISONS = {
    ast.Gt: lambda gauche, droite: gauche > droite,
    ast.Lt: lambda gauche, droite: gauche < droite,
    ast.GtE: lambda gauche, droite: gauche >= droite,
    ast.LtE: lambda gauche, droite: gauche <= droite,
    ast.Eq: lambda gauche, droite: gauche == droite,
    ast.NotEq: lambda gauche, droite: gauche != droite,
}


def _somme(*valeurs):
    return sum(valeurs)


def _moyenne(*valeurs):
    return sum(valeurs) / len(valeurs) if valeurs else 0


def _arrondi(valeur, decimales=0):
    return round(valeur, int(decimales))


FONCTIONS = {
    "SOMME": _somme,
    "MOYENNE": _moyenne,
    "MIN": lambda *valeurs: min(valeurs) if valeurs else 0,
    "MAX": lambda *valeurs: max(valeurs) if valeurs else 0,
    "ABS": lambda valeur: abs(valeur),
    "ARRONDI": _arrondi,
}

# Écritures acceptées dans les conditions, en plus de la grammaire des formules.
MOTS_LOGIQUES = {"ET": ast.And, "OU": ast.Or}


class FormuleInvalide(ValueError):
    """Expression refusée : syntaxe, écriture interdite ou référence inconnue."""


def _normaliser_condition(expression):
    """Traduit les mots français en opérateurs Python avant l'analyse."""
    remplacements = ((" ET ", " and "), (" OU ", " or "), ("≠", "!="), ("<>", "!="))
    texte = f" {expression.strip()} "
    for source, cible in remplacements:
        texte = texte.replace(source, cible)
    return texte.strip()


def _verifier(arbre, autoriser_comparaisons):
    """Parcourt l'arbre et refuse tout nœud hors liste blanche."""
    references = set()

    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Expression):
            continue
        if isinstance(noeud, ast.BinOp):
            if type(noeud.op) not in OPERATIONS:
                raise FormuleInvalide("Seules les opérations + − × ÷ sont autorisées.")
            continue
        if isinstance(noeud, ast.UnaryOp) and isinstance(noeud.op, (ast.UAdd, ast.USub)):
            continue
        if isinstance(noeud, ast.Constant):
            if isinstance(noeud.value, bool) or not isinstance(noeud.value, (int, float)):
                raise FormuleInvalide("Seuls les nombres sont acceptés comme valeurs fixes.")
            continue
        if isinstance(noeud, ast.Name):
            if noeud.id in FONCTIONS:
                continue
            references.add(noeud.id)
            continue
        if isinstance(noeud, ast.Call):
            if not isinstance(noeud.func, ast.Name) or noeud.func.id not in FONCTIONS:
                autorisees = ", ".join(sorted(FONCTIONS))
                raise FormuleInvalide(f"Fonction inconnue. Fonctions disponibles : {autorisees}.")
            if noeud.keywords:
                raise FormuleInvalide("Les arguments nommés ne sont pas acceptés.")
            continue
        if isinstance(noeud, ast.Compare):
            if not autoriser_comparaisons:
                raise FormuleInvalide("Une formule doit produire un montant, pas une comparaison.")
            if len(noeud.ops) != 1:
                raise FormuleInvalide("Une comparaison à la fois : utilisez ET pour en combiner plusieurs.")
            if type(noeud.ops[0]) not in COMPARAISONS:
                raise FormuleInvalide("Comparaison non autorisée.")
            continue
        if isinstance(noeud, ast.BoolOp):
            if not autoriser_comparaisons:
                raise FormuleInvalide("ET et OU ne s'emploient que dans une condition.")
            continue
        if isinstance(noeud, (ast.operator, ast.unaryop, ast.cmpop, ast.boolop, ast.Load)):
            continue
        raise FormuleInvalide("Cette écriture n'est pas autorisée.")

    return references


def analyser_formule(expression):
    """Valide une expression de calcul. Retourne (arbre, codes référencés)."""
    if not expression or not expression.strip():
        raise FormuleInvalide("La formule est vide.")
    try:
        arbre = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as erreur:
        raise FormuleInvalide(f"Écriture incorrecte : {erreur.msg}.") from erreur
    return arbre, _verifier(arbre, autoriser_comparaisons=False)


def analyser_condition(expression):
    """Valide une condition de règle. Retourne (arbre, codes référencés)."""
    if not expression or not expression.strip():
        raise FormuleInvalide("La condition est vide.")
    try:
        arbre = ast.parse(_normaliser_condition(expression), mode="eval")
    except SyntaxError as erreur:
        raise FormuleInvalide(f"Écriture incorrecte : {erreur.msg}.") from erreur

    references = _verifier(arbre, autoriser_comparaisons=True)
    if not isinstance(arbre.body, (ast.Compare, ast.BoolOp)):
        raise FormuleInvalide("Une condition doit comparer deux valeurs, par exemple PRESSION > 100.")
    return arbre, references


def evaluer(arbre, valeurs):
    """Évalue un arbre déjà validé. Une référence absente vaut zéro."""

    def visiter(noeud):
        if isinstance(noeud, ast.Expression):
            return visiter(noeud.body)
        if isinstance(noeud, ast.Constant):
            return noeud.value
        if isinstance(noeud, ast.Name):
            valeur = valeurs.get(noeud.id, 0)
            return 0 if valeur is None else valeur
        if isinstance(noeud, ast.UnaryOp):
            valeur = visiter(noeud.operand)
            return -valeur if isinstance(noeud.op, ast.USub) else valeur
        if isinstance(noeud, ast.BinOp):
            return OPERATIONS[type(noeud.op)](visiter(noeud.left), visiter(noeud.right))
        if isinstance(noeud, ast.Call):
            return FONCTIONS[noeud.func.id](*[visiter(argument) for argument in noeud.args])
        if isinstance(noeud, ast.Compare):
            return COMPARAISONS[type(noeud.ops[0])](visiter(noeud.left), visiter(noeud.comparators[0]))
        if isinstance(noeud, ast.BoolOp):
            valeurs_operandes = [visiter(operande) for operande in noeud.values]
            return all(valeurs_operandes) if isinstance(noeud.op, ast.And) else any(valeurs_operandes)
        raise FormuleInvalide("Expression non évaluable.")

    return visiter(arbre)


def ordonner(rubriques, codes_de_contexte=()):
    """Ordonne les rubriques calculées selon leurs dépendances.

    `rubriques` est une liste de dictionnaires : code, mode, formule.
    `codes_de_contexte` désigne les valeurs fournies par le dossier sans
    figurer au cadre — l'échéance projetée, par exemple, qui vient de la
    demande. Une formule a le droit de s'y référer.

    Retourne la liste des codes calculés dans l'ordre d'évaluation et leurs
    arbres. Lève FormuleInvalide sur une dépendance inconnue ou circulaire.
    """
    connues = {rubrique["code"] for rubrique in rubriques} | set(codes_de_contexte)
    dependances, arbres = {}, {}

    for rubrique in rubriques:
        if rubrique["mode"] != "CALCUL":
            continue
        arbre, references = analyser_formule(rubrique.get("formule", ""))
        inconnues = references - connues
        if inconnues:
            raise FormuleInvalide(
                f"{rubrique['code']} : rubrique(s) inconnue(s) — {', '.join(sorted(inconnues))}.")
        dependances[rubrique["code"]] = references
        arbres[rubrique["code"]] = arbre

    ordre, en_cours, resolus = [], set(), set()

    def resoudre(code, chemin):
        if code in resolus:
            return
        if code in en_cours:
            boucle = " → ".join([*chemin, code])
            raise FormuleInvalide(f"Dépendance circulaire détectée : {boucle}.")
        en_cours.add(code)
        for dependance in sorted(dependances.get(code, ())):
            if dependance in dependances:
                resoudre(dependance, [*chemin, code])
        en_cours.discard(code)
        resolus.add(code)
        ordre.append(code)

    for code in dependances:
        resoudre(code, [])
    return ordre, arbres
