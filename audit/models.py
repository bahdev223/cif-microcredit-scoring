from django.db import models
from credits.models import CreditApplication


class AuditLog(models.Model):
    application = models.ForeignKey(CreditApplication, on_delete=models.CASCADE, related_name="audit_logs")
    event_type = models.CharField(max_length=60)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
