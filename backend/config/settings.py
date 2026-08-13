import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RACINE_PROJET = BASE_DIR.parent
SECRET_KEY = os.environ.get("CIF_SECRET_KEY", "development-only-change-before-production")
DEBUG = os.environ.get("CIF_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.environ.get("CIF_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "drf_spectacular",
    "clients",
    "analyse",
    "cadres",
    "credits",
    "audit",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [RACINE_PROJET / "frontend" / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.environ.get("CIF_CHEMIN_BASE_DONNEES", RACINE_PROJET / "db.sqlite3")}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Bamako"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATICFILES_DIRS = [RACINE_PROJET / "frontend" / "static"]

# Pièces jointes des dossiers clients. Le dossier est hors du dépôt : il
# contiendrait, en usage réel, des documents personnels.
MEDIA_URL = "documents/"
MEDIA_ROOT = Path(os.environ.get("CIF_REPERTOIRE_DOCUMENTS", RACINE_PROJET.parent / "cif-microcredit-donnees-locales" / "documents"))
TAILLE_MAXIMALE_DOCUMENT = 5 * 1024 * 1024
EXTENSIONS_DOCUMENTS_AUTORISEES = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
REST_FRAMEWORK = {"DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema"}
SPECTACULAR_SETTINGS = {"TITLE": "API CIF Microcrédit", "DESCRIPTION": "API de gestion du portefeuille et d'import CSV.", "VERSION": "1.0.0"}
