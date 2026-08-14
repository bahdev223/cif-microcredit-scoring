from django.db import models


class Institution(models.Model):
    nom = models.CharField(max_length=160, default="CIF Microfinance")
    sigle = models.CharField(max_length=30, default="CIF")
    ville = models.CharField(max_length=80, blank=True)
    pays = models.CharField(max_length=80, default="Mali")
    modifie_le = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom


class Client(models.Model):
    """Identité et activité, jamais la situation financière.

    Une situation économique appartient à une date, pas à une personne : ce que
    Fatou gagnait en 2023 n'est pas ce qu'elle gagne aujourd'hui. Les recettes,
    charges et engagements sont donc relevés sur chaque demande, horodatés, et
    conservés là. Les champs financiers qui vivaient ici ont été retirés pour
    cette raison.
    """

    identifiant_source = models.CharField(max_length=40, blank=True, unique=True, null=True)
    identifiant_institution_source = models.CharField(max_length=30, blank=True)
    nom_complet = models.CharField(max_length=160)
    secteur_activite = models.CharField(max_length=80)
    anciennete_activite_mois = models.PositiveIntegerField()
    cree_le = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom_complet


def chemin_document(instance, nom_fichier):
    return f"clients/{instance.client_id}/{nom_fichier}"


class DocumentDossier(models.Model):
    """Pièce jointe au dossier d'un client.

    Les catégories sont celles qu'une institution demande couramment. Elles
    doivent être confirmées avec elle : chaque produit de crédit peut exiger
    des pièces différentes. Aucune lecture automatique n'est faite du contenu.
    """

    CATEGORIES = (
        ("piece_identite", "Pièce d'identité"),
        ("justificatif_activite", "Justificatif d'activité"),
        ("photo", "Photo"),
        ("autre", "Autre document"),
    )

    client = models.ForeignKey("Client", on_delete=models.CASCADE, related_name="documents")
    categorie = models.CharField(max_length=40, choices=CATEGORIES)
    fichier = models.FileField(upload_to=chemin_document)
    nom_original = models.CharField(max_length=200)
    taille_octets = models.PositiveIntegerField(default=0)
    televerse_le = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_categorie_display()} — {self.nom_original}"


class ActiviteImportee(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="activites_importees")
    identifiant_source = models.CharField(max_length=40, unique=True)
    secteur = models.CharField(max_length=80)
    libelle = models.CharField(max_length=160, blank=True)
    est_principale = models.BooleanField(default=True)
    date_debut = models.DateField(null=True, blank=True)
