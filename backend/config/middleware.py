"""Interdit la mise en cache des fichiers statiques en développement.

Le frontend est découpé en modules ES : `app.js` importe `pilotage.js`, qui
importe `noyau.js`. Ces URL d'import n'ont pas de paramètre de version, si bien
qu'ajouter `?v=13` au script principal ne rafraîchit rien du tout. On voit
alors s'afficher l'ancien code alors que le fichier a changé sur le disque —
et on cherche le défaut au mauvais endroit.

Ce middleware ne s'active qu'en DEBUG. En production, les fichiers statiques
sont servis par le serveur web, avec ses propres règles de cache.
"""

from django.conf import settings


class SansCacheEnDeveloppement:
    def __init__(self, reponse_suivante):
        self.reponse_suivante = reponse_suivante
        # STATIC_URL peut être écrit « static/ » sans barre initiale, alors que
        # le chemin d'une requête commence toujours par « / ».
        prefixe = settings.STATIC_URL or "/static/"
        self.prefixe = "/" + prefixe.strip("/") + "/"

    def __call__(self, requete):
        reponse = self.reponse_suivante(requete)
        if settings.DEBUG and requete.path.startswith(self.prefixe):
            reponse["Cache-Control"] = "no-store, must-revalidate"
        return reponse
