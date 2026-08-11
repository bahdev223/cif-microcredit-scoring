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
