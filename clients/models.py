from django.db import models


class Client(models.Model):
    full_name = models.CharField(max_length=160)
    sector = models.CharField(max_length=80)
    monthly_income = models.PositiveIntegerField()
    monthly_expenses = models.PositiveIntegerField()
    business_age_months = models.PositiveIntegerField()
    late_payments = models.PositiveSmallIntegerField(default=0)
    tontine_regularity = models.CharField(max_length=20, default="unknown")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
