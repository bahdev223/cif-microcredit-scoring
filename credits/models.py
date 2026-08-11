from django.db import models
from clients.models import Client


class CreditApplication(models.Model):
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="applications")
    amount = models.PositiveIntegerField()
    term_months = models.PositiveSmallIntegerField(default=12)
    risk_score = models.PositiveSmallIntegerField(null=True, blank=True)
    risk_level = models.CharField(max_length=20, blank=True)
    decision = models.CharField(max_length=20, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def estimated_installment(self):
        return round(self.amount / self.term_months)
