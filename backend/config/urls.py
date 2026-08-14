from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="accueil"),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema-api"),
    path("api/documentation/", SpectacularSwaggerView.as_view(url_name="schema-api"), name="documentation-api"),
]

if settings.DEBUG:
    # Service des pièces jointes en développement uniquement. En production,
    # elles doivent être servies par le serveur web, avec un contrôle d'accès.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Les fichiers statiques passent par une route ordinaire afin que le
    # middleware anti-cache s'applique. Lancé sans --nostatic, runserver les
    # intercepte avant les middlewares et cette route n'est jamais atteinte :
    # le navigateur peut alors servir d'anciens modules ES.
    from django.contrib.staticfiles.views import serve as servir_fichier_statique
    from django.urls import re_path

    urlpatterns += [re_path(r"^static/(?P<path>.*)$", servir_fichier_statique)]
