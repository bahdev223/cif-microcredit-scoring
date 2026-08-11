from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("audit", "0001_initial"), ("credits", "0002_franciser_demande_credit")]

    operations = [
        migrations.RenameModel(old_name="AuditLog", new_name="JournalAudit"),
        migrations.RenameField(model_name="journalaudit", old_name="application", new_name="demande_credit"),
        migrations.RenameField(model_name="journalaudit", old_name="event_type", new_name="type_evenement"),
        migrations.RenameField(model_name="journalaudit", old_name="payload", new_name="contenu"),
        migrations.RenameField(model_name="journalaudit", old_name="created_at", new_name="cree_le"),
        migrations.AlterField(model_name="journalaudit", name="demande_credit", field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="journaux_audit", to="credits.demandecredit")),
    ]
