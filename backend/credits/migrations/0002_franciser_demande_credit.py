from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("credits", "0001_initial")]

    operations = [
        migrations.RenameModel(old_name="CreditApplication", new_name="DemandeCredit"),
        migrations.RenameField(model_name="demandecredit", old_name="amount", new_name="montant_demande"),
        migrations.RenameField(model_name="demandecredit", old_name="term_months", new_name="duree_mois"),
        migrations.RenameField(model_name="demandecredit", old_name="risk_score", new_name="score_risque"),
        migrations.RenameField(model_name="demandecredit", old_name="risk_level", new_name="niveau_risque"),
        migrations.RenameField(model_name="demandecredit", old_name="decision", new_name="decision_agent"),
        migrations.RenameField(model_name="demandecredit", old_name="created_at", new_name="cree_le"),
        migrations.AlterField(model_name="demandecredit", name="client", field=models.ForeignKey(on_delete=models.deletion.PROTECT, related_name="demandes_credit", to="clients.client")),
        migrations.AlterField(model_name="demandecredit", name="decision_agent", field=models.CharField(default="EN_ATTENTE", max_length=20)),
    ]
