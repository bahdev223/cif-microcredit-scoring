from django.db import models
from clients.models import Client


class DemandeCredit(models.Model):
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="demandes_credit")
    montant_demande = models.PositiveIntegerField()
    duree_mois = models.PositiveSmallIntegerField(default=12)
    score_risque = models.PositiveSmallIntegerField(null=True, blank=True)
    niveau_risque = models.CharField(max_length=20, blank=True)
    decision_agent = models.CharField(max_length=20, default="EN_ATTENTE")
    cree_le = models.DateTimeField(auto_now_add=True)

    @property
    def echeance_estimee(self):
        return round(self.montant_demande / self.duree_mois)


class CreditImporte(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="credits_importes")
    identifiant_source = models.CharField(max_length=40, unique=True)
    identifiant_demande_source = models.CharField(max_length=40, blank=True)
    montant_decaisse = models.PositiveIntegerField(default=0)
    duree_mois = models.PositiveSmallIntegerField(default=0)
    date_decaissement = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=30, default="IMPORTED")


class EcheanceImportee(models.Model):
    credit = models.ForeignKey(CreditImporte, on_delete=models.CASCADE, related_name="echeances")
    identifiant_source = models.CharField(max_length=40, unique=True)
    numero = models.PositiveSmallIntegerField(default=0)
    date_exigible = models.DateField(null=True, blank=True)
    montant_du = models.PositiveIntegerField(default=0)


class PaiementImporte(models.Model):
    credit = models.ForeignKey(CreditImporte, on_delete=models.CASCADE, related_name="paiements")
    echeance = models.ForeignKey(EcheanceImportee, on_delete=models.SET_NULL, null=True, blank=True, related_name="paiements")
    identifiant_source = models.CharField(max_length=40, unique=True)
    date_paiement = models.DateField(null=True, blank=True)
    montant_paye = models.PositiveIntegerField(default=0)
    canal = models.CharField(max_length=40, blank=True)
