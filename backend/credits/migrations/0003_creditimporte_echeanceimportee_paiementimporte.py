from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("clients", "0004_client_identifiant_source_client_identifiant_institution_source"), ("credits", "0002_franciser_demande_credit")]
    operations = [
        migrations.CreateModel(name="CreditImporte", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("identifiant_source", models.CharField(max_length=40, unique=True)),
            ("identifiant_demande_source", models.CharField(blank=True, max_length=40)),
            ("montant_decaisse", models.PositiveIntegerField(default=0)),
            ("duree_mois", models.PositiveSmallIntegerField(default=0)),
            ("date_decaissement", models.DateField(blank=True, null=True)),
            ("statut", models.CharField(default="IMPORTED", max_length=30)),
            ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="credits_importes", to="clients.client")),
        ]),
        migrations.CreateModel(name="EcheanceImportee", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("identifiant_source", models.CharField(max_length=40, unique=True)),
            ("numero", models.PositiveSmallIntegerField(default=0)),
            ("date_exigible", models.DateField(blank=True, null=True)),
            ("montant_du", models.PositiveIntegerField(default=0)),
            ("credit", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="echeances", to="credits.creditimporte")),
        ]),
        migrations.CreateModel(name="PaiementImporte", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("identifiant_source", models.CharField(max_length=40, unique=True)),
            ("date_paiement", models.DateField(blank=True, null=True)),
            ("montant_paye", models.PositiveIntegerField(default=0)),
            ("canal", models.CharField(blank=True, max_length=40)),
            ("credit", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="paiements", to="credits.creditimporte")),
            ("echeance", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="paiements", to="credits.echeanceimportee")),
        ]),
    ]
