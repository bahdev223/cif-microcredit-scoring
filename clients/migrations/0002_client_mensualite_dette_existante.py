from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("clients", "0001_initial")]

    operations = [
        migrations.RenameField(model_name="client", old_name="full_name", new_name="nom_complet"),
        migrations.RenameField(model_name="client", old_name="sector", new_name="secteur_activite"),
        migrations.RenameField(model_name="client", old_name="monthly_income", new_name="revenu_mensuel"),
        migrations.RenameField(model_name="client", old_name="monthly_expenses", new_name="charges_mensuelles"),
        migrations.RenameField(model_name="client", old_name="business_age_months", new_name="anciennete_activite_mois"),
        migrations.RenameField(model_name="client", old_name="late_payments", new_name="nombre_retards"),
        migrations.RenameField(model_name="client", old_name="tontine_regularity", new_name="regularite_tontine"),
        migrations.RenameField(model_name="client", old_name="created_at", new_name="cree_le"),
        migrations.AlterField(model_name="client", name="regularite_tontine", field=models.CharField(default="inconnue", max_length=20)),
        migrations.AddField(
            model_name="client",
            name="mensualite_dette_existante",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
