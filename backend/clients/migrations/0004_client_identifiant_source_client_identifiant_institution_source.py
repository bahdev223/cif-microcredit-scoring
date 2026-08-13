from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("clients", "0003_institution")]
    operations = [
        migrations.AddField(model_name="client", name="identifiant_source", field=models.CharField(blank=True, max_length=40, null=True, unique=True)),
        migrations.AddField(model_name="client", name="identifiant_institution_source", field=models.CharField(blank=True, max_length=30)),
    ]
