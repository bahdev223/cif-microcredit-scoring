"""Les cinq objets du constructeur de cadres d'analyse.

    CadreAnalyse ──< SectionAnalyse ──< RubriqueAnalyse ──1 FormuleAnalyse
          └────────< RegleAnalyse

Aucun de ces objets ne connaît de secteur d'activité, de produit de crédit ni
de politique d'octroi. Ils décrivent une méthode de calcul ; c'est tout.
"""

from django.core.exceptions import ValidationError
from django.db import models

from .calcul import FormuleInvalide, analyser_condition, analyser_formule


class CadreAnalyse(models.Model):
    """Méthode d'analyse financière définie par l'institution.

    Un cadre publié devient immuable. Pour le faire évoluer, on le duplique en
    une nouvelle version : les analyses déjà produites restent reproductibles.
    """

    STATUTS = (("BROUILLON", "Brouillon"), ("PUBLIE", "Publié"), ("ARCHIVE", "Archivé"))

    code = models.CharField(max_length=40)
    nom = models.CharField(max_length=120)
    description = models.CharField(max_length=300, blank=True)
    version = models.PositiveSmallIntegerField(default=1)
    statut = models.CharField(max_length=20, choices=STATUTS, default="BROUILLON")
    cree_le = models.DateTimeField(auto_now_add=True)
    publie_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("code", "version")
        ordering = ("code", "-version")

    def __str__(self):
        return self.reference

    @property
    def reference(self):
        return f"{self.nom} v{self.version}"

    @property
    def modifiable(self):
        return self.statut == "BROUILLON"

    def rubriques_ordonnees(self):
        return list(
            RubriqueAnalyse.objects
            .filter(section__cadre=self)
            .select_related("section", "formule")
            .order_by("section__ordre", "ordre", "id")
        )

    def definition(self):
        """Représentation à plat consommée par le moteur de calcul."""
        return [{
            "code": rubrique.code,
            "nom": rubrique.nom,
            "mode": rubrique.mode,
            "type": rubrique.type_valeur,
            "sens": rubrique.sens,
            "obligatoire": rubrique.obligatoire,
            "unite": rubrique.unite,
            "section_code": rubrique.section.code,
            "section_nom": rubrique.section.nom,
            "role": rubrique.role,
            "formule": rubrique.expression,
        } for rubrique in self.rubriques_ordonnees()]

    def definition_regles(self):
        return [{
            "code": regle.code,
            "nom": regle.nom,
            "condition": regle.condition,
            "resultat": regle.resultat,
            "message": regle.message,
        } for regle in self.regles.order_by("ordre", "id")]

    def dupliquer(self):
        """Crée la version suivante, à l'identique, en brouillon."""
        derniere = CadreAnalyse.objects.filter(code=self.code).order_by("-version").first()
        copie = CadreAnalyse.objects.create(
            code=self.code,
            nom=self.nom,
            description=self.description,
            version=derniere.version + 1,
            statut="BROUILLON",
        )
        for section in self.sections.order_by("ordre", "id"):
            nouvelle = SectionAnalyse.objects.create(
                cadre=copie, code=section.code, nom=section.nom, ordre=section.ordre)
            for rubrique in section.rubriques.order_by("ordre", "id"):
                copie_rubrique = RubriqueAnalyse.objects.create(
                    section=nouvelle,
                    code=rubrique.code,
                    nom=rubrique.nom,
                    mode=rubrique.mode,
                    type_valeur=rubrique.type_valeur,
                    sens=rubrique.sens,
                    unite=rubrique.unite,
                    periodicite=rubrique.periodicite,
                    source=rubrique.source,
                    obligatoire=rubrique.obligatoire,
                    role=rubrique.role,
                    ordre=rubrique.ordre,
                )
                if hasattr(rubrique, "formule"):
                    FormuleAnalyse.objects.create(
                        rubrique=copie_rubrique, expression=rubrique.formule.expression)
        for regle in self.regles.order_by("ordre", "id"):
            RegleAnalyse.objects.create(
                cadre=copie,
                code=regle.code,
                nom=regle.nom,
                condition=regle.condition,
                resultat=regle.resultat,
                message=regle.message,
                ordre=regle.ordre,
            )
        return copie

    def publier(self):
        """Rend le cadre applicable et archive la version publiée précédente."""
        from django.utils import timezone

        CadreAnalyse.objects.filter(code=self.code, statut="PUBLIE").exclude(pk=self.pk).update(statut="ARCHIVE")
        self.statut = "PUBLIE"
        self.publie_le = timezone.now()
        self.save(update_fields=["statut", "publie_le"])


class SectionAnalyse(models.Model):
    """Regroupement de rubriques : activité, ménage, engagements, capacité…"""

    cadre = models.ForeignKey(CadreAnalyse, on_delete=models.CASCADE, related_name="sections")
    code = models.CharField(max_length=40)
    nom = models.CharField(max_length=120)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("cadre", "code")
        ordering = ("ordre", "id")

    def __str__(self):
        return self.nom


class RubriqueAnalyse(models.Model):
    """Une ligne du cadre : saisie, calculée, ou simple information."""

    MODES = (("SAISIE", "Saisie"), ("CALCUL", "Calculée"), ("INFORMATION", "Information"))
    TYPES = (
        ("MONTANT", "Montant"), ("NOMBRE", "Nombre"), ("POURCENTAGE", "Pourcentage"),
        ("DATE", "Date"), ("CHOIX", "Choix"), ("BOOLEEN", "Oui / non"), ("TEXTE", "Texte"),
    )
    SENS = (("CREDIT", "S'ajoute"), ("DEBIT", "Se retranche"), ("RESULTAT", "Résultat"), ("NEUTRE", "Neutre"))
    SOURCES = (("DECLARATIVE", "Déclarative"), ("IMPORTEE", "Importée"), ("CALCULEE", "Calculée"))
    # Une institution nomme ses rubriques comme elle veut. Pour que la
    # plateforme sache laquelle porte la marge ou la pression, la rubrique
    # déclare son rôle : c'est ce qui évite de coder des noms en dur.
    ROLES = (
        ("", "Aucun rôle particulier"),
        ("MARGE_DISPONIBLE", "Marge disponible"),
        ("PRESSION_REMBOURSEMENT", "Pression de remboursement"),
        ("RESULTAT_ACTIVITE", "Résultat de l'activité"),
    )
    PERIODICITES = (
        ("MENSUELLE", "Mensuelle"), ("CAMPAGNE", "Par campagne"),
        ("ANNUELLE", "Annuelle"), ("PONCTUELLE", "Ponctuelle"),
    )

    section = models.ForeignKey(SectionAnalyse, on_delete=models.CASCADE, related_name="rubriques")
    code = models.CharField(max_length=40)
    nom = models.CharField(max_length=140)
    mode = models.CharField(max_length=20, choices=MODES, default="SAISIE")
    type_valeur = models.CharField(max_length=20, choices=TYPES, default="MONTANT")
    sens = models.CharField(max_length=20, choices=SENS, default="CREDIT")
    unite = models.CharField(max_length=20, blank=True)
    periodicite = models.CharField(max_length=20, choices=PERIODICITES, default="MENSUELLE")
    source = models.CharField(max_length=20, choices=SOURCES, default="DECLARATIVE")
    obligatoire = models.BooleanField(default=False)
    role = models.CharField(max_length=30, choices=ROLES, blank=True)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("ordre", "id")

    def __str__(self):
        return f"{self.code} — {self.nom}"

    @property
    def expression(self):
        return self.formule.expression if hasattr(self, "formule") else ""

    def clean(self):
        if self.mode == "CALCUL" and not hasattr(self, "formule"):
            raise ValidationError({"mode": "Une rubrique calculée doit porter une formule."})
        if self.mode != "CALCUL" and hasattr(self, "formule"):
            raise ValidationError({"mode": "Seule une rubrique calculée peut porter une formule."})


class FormuleAnalyse(models.Model):
    """Expression de calcul rattachée à une rubrique calculée."""

    rubrique = models.OneToOneField(RubriqueAnalyse, on_delete=models.CASCADE, related_name="formule")
    expression = models.CharField(max_length=400)
    modifie_le = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.rubrique.code} = {self.expression}"

    def clean(self):
        try:
            analyser_formule(self.expression)
        except FormuleInvalide as erreur:
            raise ValidationError({"expression": str(erreur)}) from erreur


class RegleAnalyse(models.Model):
    """Interprétation d'un résultat, définie par l'institution.

    Une règle ne calcule rien : elle lit les résultats du moteur de calcul et
    signale ce qui mérite l'attention de l'agent. Les seuils qu'elle emploie
    appartiennent à l'institution, jamais à l'application.
    """

    RESULTATS = (
        ("POINT_ATTENTION", "Point d'attention"),
        ("POINT_FAVORABLE", "Point favorable"),
        ("INFORMATION", "Information"),
        ("DOSSIER_INCOMPLET", "Dossier incomplet"),
    )

    cadre = models.ForeignKey(CadreAnalyse, on_delete=models.CASCADE, related_name="regles")
    code = models.CharField(max_length=40)
    nom = models.CharField(max_length=140)
    condition = models.CharField(max_length=400)
    resultat = models.CharField(max_length=30, choices=RESULTATS, default="POINT_ATTENTION")
    message = models.CharField(max_length=300)
    ordre = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("cadre", "code")
        ordering = ("ordre", "id")

    def __str__(self):
        return self.nom

    def clean(self):
        try:
            analyser_condition(self.condition)
        except FormuleInvalide as erreur:
            raise ValidationError({"condition": str(erreur)}) from erreur
