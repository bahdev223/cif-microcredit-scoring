from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0002_client_mensualite_dette_existante"),
    ]

    operations = [
        migrations.CreateModel(
            name="Institution",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nom", models.CharField(default="CIF Microfinance", max_length=160)),
                ("sigle", models.CharField(default="CIF", max_length=30)),
                ("ville", models.CharField(blank=True, max_length=80)),
                ("pays", models.CharField(default="Mali", max_length=80)),
                ("modifie_le", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
