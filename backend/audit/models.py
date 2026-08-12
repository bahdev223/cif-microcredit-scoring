from django.db import models
from credits.models import DemandeCredit


class JournalAudit(models.Model):
    demande_credit = models.ForeignKey(DemandeCredit, on_delete=models.CASCADE, related_name="journaux_audit")
    type_evenement = models.CharField(max_length=60)
    contenu = models.JSONField()
    cree_le = models.DateTimeField(auto_now_add=True)
