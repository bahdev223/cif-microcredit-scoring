from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("clients", "0004_client_identifiant_source_client_identifiant_institution_source")]
    operations = [migrations.CreateModel(name="ActiviteImportee", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("identifiant_source", models.CharField(max_length=40, unique=True)),
        ("secteur", models.CharField(max_length=80)),
        ("libelle", models.CharField(blank=True, max_length=160)),
        ("est_principale", models.BooleanField(default=True)),
        ("date_debut", models.DateField(blank=True, null=True)),
        ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activites_importees", to="clients.client")),
    ])]
