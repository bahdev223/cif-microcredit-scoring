from django.db import models


class Client(models.Model):
    nom_complet = models.CharField(max_length=160)
    secteur_activite = models.CharField(max_length=80)
    revenu_mensuel = models.PositiveIntegerField()
    charges_mensuelles = models.PositiveIntegerField()
    mensualite_dette_existante = models.PositiveIntegerField(default=0)
    anciennete_activite_mois = models.PositiveIntegerField()
    nombre_retards = models.PositiveSmallIntegerField(default=0)
    regularite_tontine = models.CharField(max_length=20, default="inconnue")
    cree_le = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom_complet
