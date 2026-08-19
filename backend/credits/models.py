from django.db import models
from clients.models import Client


class ProduitCredit(models.Model):
    """Produit proposé par l'institution.

    Aucun produit n'est livré par défaut : les montants, durées et conditions
    appartiennent à chaque institution et doivent être saisis avec elle.
    """

    code = models.CharField(max_length=30, unique=True)
    libelle = models.CharField(max_length=120)
    montant_min = models.PositiveIntegerField(default=0)
    montant_max = models.PositiveIntegerField(default=0)
    duree_min_mois = models.PositiveSmallIntegerField(default=0)
    duree_max_mois = models.PositiveSmallIntegerField(default=0)
    secteurs_vises = models.CharField(max_length=200, blank=True)
    cadre_analyse = models.ForeignKey(
        "cadres.CadreAnalyse", on_delete=models.SET_NULL, null=True, blank=True, related_name="produits",
        help_text="Méthode d'analyse financière appliquée aux demandes portant ce produit.",
    )
    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.libelle


class DemandeCredit(models.Model):
    """Dossier de demande, avec la situation du client telle que connue ce jour-là.

    Les montants sont recopiés dans la demande au lieu d'être lus sur la fiche
    client : une instruction doit rester lisible des mois plus tard, avec les
    informations dont l'agent disposait réellement au moment de décider.
    """

    DECISIONS = (
        ("EN_ATTENTE", "En attente"),
        ("A_REVOIR", "À revoir"),
        ("FAVORABLE", "Favorable"),
        ("DEFAVORABLE", "Défavorable"),
    )

    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="demandes_credit")
    produit = models.ForeignKey(ProduitCredit, on_delete=models.SET_NULL, null=True, blank=True, related_name="demandes")
    montant_demande = models.PositiveIntegerField()
    duree_mois = models.PositiveSmallIntegerField(default=12)
    objet_credit = models.CharField(max_length=160, blank=True)

    # Situation relevée au moment de l'instruction.
    recettes_activite = models.PositiveIntegerField(default=0)
    charges_activite = models.PositiveIntegerField(default=0)
    autres_revenus_menage = models.PositiveIntegerField(default=0)
    charges_menage = models.PositiveIntegerField(default=0)
    mensualite_dette_existante = models.PositiveIntegerField(default=0)
    anciennete_activite_mois = models.PositiveIntegerField(default=0)
    saisonnalite_activite = models.CharField(max_length=40, blank=True)

    # Cadre qui a servi à analyser cette demande, dans sa version d'alors : une
    # instruction reste reproductible même si l'institution fait évoluer sa
    # méthode ensuite.
    cadre_analyse = models.ForeignKey(
        "cadres.CadreAnalyse", on_delete=models.SET_NULL, null=True, blank=True, related_name="demandes")
    valeurs_cadre = models.JSONField(default=dict, blank=True)

    observations_agent = models.TextField(blank=True)
    decision_agent = models.CharField(max_length=20, choices=DECISIONS, default="EN_ATTENTE")
    motif_decision = models.CharField(max_length=160, blank=True)
    date_decision = models.DateTimeField(null=True, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    @property
    def echeance_estimee(self):
        """Montant divisé par la durée, hors intérêts et frais.

        La formule réelle dépend du produit et de la tarification de
        l'institution ; elle doit être confirmée avec elle.
        """
        return round(self.montant_demande / self.duree_mois) if self.duree_mois else 0

    @property
    def marge_estimee(self):
        return (self.recettes_activite + self.autres_revenus_menage
                - self.charges_activite - self.charges_menage - self.mensualite_dette_existante)


class CreditImporte(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="credits_importes")
    identifiant_source = models.CharField(max_length=40)
    identifiant_demande_source = models.CharField(max_length=40, blank=True)
    montant_decaisse = models.PositiveIntegerField(default=0)
    duree_mois = models.PositiveSmallIntegerField(default=0)
    date_decaissement = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=30, default="IMPORTED")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("client", "identifiant_source"), name="credit_source_unique_par_client")]


class EcheanceImportee(models.Model):
    credit = models.ForeignKey(CreditImporte, on_delete=models.CASCADE, related_name="echeances")
    identifiant_source = models.CharField(max_length=40)
    numero = models.PositiveSmallIntegerField(default=0)
    date_exigible = models.DateField(null=True, blank=True)
    montant_du = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("credit", "identifiant_source"), name="echeance_source_unique_par_credit")]


class PaiementImporte(models.Model):
    credit = models.ForeignKey(CreditImporte, on_delete=models.CASCADE, related_name="paiements")
    echeance = models.ForeignKey(EcheanceImportee, on_delete=models.SET_NULL, null=True, blank=True, related_name="paiements")
    identifiant_source = models.CharField(max_length=40)
    date_paiement = models.DateField(null=True, blank=True)
    montant_paye = models.PositiveIntegerField(default=0)
    canal = models.CharField(max_length=40, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("credit", "identifiant_source"), name="paiement_source_unique_par_credit")]


class DemandeImportee(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="demandes_importees")
    identifiant_source = models.CharField(max_length=40)
    montant = models.PositiveIntegerField(default=0)
    duree_mois = models.PositiveSmallIntegerField(default=0)
    date_demande = models.DateField(null=True, blank=True)
    objet = models.CharField(max_length=120, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("client", "identifiant_source"), name="demande_source_unique_par_client")]
