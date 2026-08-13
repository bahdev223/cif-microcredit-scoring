from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("clients", "0005_activiteimportee"), ("credits", "0003_creditimporte_echeanceimportee_paiementimporte")]
    operations = [migrations.CreateModel(name="DemandeImportee", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("identifiant_source", models.CharField(max_length=40, unique=True)),
        ("montant", models.PositiveIntegerField(default=0)),
        ("duree_mois", models.PositiveSmallIntegerField(default=0)),
        ("date_demande", models.DateField(blank=True, null=True)),
        ("objet", models.CharField(blank=True, max_length=120)),
        ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="demandes_importees", to="clients.client")),
    ])]
