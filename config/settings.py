"""Settings de AquaLab.

Los secretos y la base de datos se leen de variables de entorno (ver `.env.example`).
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(nombre, por_defecto):
    return os.environ.get(nombre, por_defecto).lower() in ("1", "true", "yes")


SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = _env_bool("DEBUG", "False")

ALLOWED_HOSTS = [h for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "usuarios",
    "clientes",
    "muestras",
    "pruebas",
    "estudios",
    "informes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "usuarios.middleware.NoAlmacenarSesionMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "usuarios.context_processors.contexto_sesion",
            ],
            # Filtros compartidos de la interfaz: {% load ui %}.
            "libraries": {"ui": "config.ui"},
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(conn_max_age=600),
}

AUTH_USER_MODEL = "usuarios.Usuario"

LOGIN_URL = "usuarios:login"
LOGOUT_REDIRECT_URL = "usuarios:login"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
# Estilos, fuentes, imágenes y JS compartidos. El CSS se compila con Tailwind (ver README).
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Correo (US 1.3). Por defecto se muestra en la consola; para enviar de verdad, configurar SMTP en
# `.env` (ver `.env.example`). En los tests, pytest-django usa siempre el backend en memoria.
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = _env_bool("EMAIL_USE_TLS", "True")
EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", "10"))
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "AquaLab <no-responder@aqualab.local>")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "usuarios.notificaciones": {"handlers": ["console"], "level": "INFO"},
    },
}

# Datos institucionales del laboratorio que encabezan los informes (US 7.2). Son de ejemplo (DEMO):
# se reemplazan acá cuando el laboratorio los envíe. Cada informe guarda una copia al emitirse.
# `logo` es una referencia: "aqualab" usa la marca de AquaLab; el del laboratorio será la ruta de
# su imagen en static/, con un nombre nuevo si cambia, para no alterar los informes emitidos.
AQUALAB_LABORATORIO = {
    "nombre": "Laboratorio de Análisis de Agua (DEMO)",
    "direccion": "Av. Paseo Colón 850, Ciudad de Buenos Aires (DEMO)",
    "matricula": "Habilitación N° 0000 (DEMO)",
    "responsable_tecnico": "Bioq. Responsable Técnico (DEMO)",
    "logo": "aqualab",
}
