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

# Producción (Render): AQUALAB_ENTORNO=produccion activa HTTPS y cookies seguras. En desarrollo y
# en los tests no se define (ver `.env.example` y `render.yaml`).
PRODUCCION = os.environ.get("AQUALAB_ENTORNO", "").strip().lower() == "produccion"
if PRODUCCION and DEBUG:
    raise RuntimeError("AQUALAB_ENTORNO=produccion no admite DEBUG=True.")

CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o]

# Render define el dominio público del servicio (por ejemplo, aqualab.onrender.com).
_HOST_RENDER = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
if _HOST_RENDER:
    ALLOWED_HOSTS.append(_HOST_RENDER)
    CSRF_TRUSTED_ORIGINS.append(f"https://{_HOST_RENDER}")

if PRODUCCION:
    # Render termina el HTTPS en su proxy y avisa el esquema original en X-Forwarded-Proto.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24

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
    "asistente",  # US 10.1
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Sirve los estáticos con DEBUG=False (producción); va justo después de SecurityMiddleware.
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
                "asistente.context_processors.asistente",
            ],
            # Filtros compartidos de la interfaz: {% load ui %}.
            "libraries": {"ui": "config.ui"},
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    # conn_health_checks: la base de Render puede cortar conexiones mientras el servicio duerme.
    "default": dj_database_url.config(conn_max_age=600, conn_health_checks=True),
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
# Destino de `collectstatic` (lo corre el Dockerfile); en producción WhiteNoise sirve de ahí los
# archivos comprimidos. Sin hash en el nombre (CompressedManifest...): rechaza el `.map` que nombra
# Chart.js y no exige correr `collectstatic` en desarrollo ni en los tests.
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

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
        "estudios.notificaciones": {"handlers": ["console"], "level": "INFO"},
        "informes.envios": {"handlers": ["console"], "level": "INFO"},
        "asistente": {"handlers": ["console"], "level": "INFO"},
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
    "logo": "aqualab",
}

# Regla de desvíos (US 8.2): hay desvío si un resultado sin validar difiere en más de `umbral` %
# del promedio de los últimos `cantidad` resultados validados de su origen. Es la regla inicial, a
# confirmar con el laboratorio, y este es el único lugar donde se define (la lee
# estudios/desvios.py).
AQUALAB_DESVIOS = {"umbral": "30", "cantidad": 3}

# Base de los enlaces absolutos de los correos que se generan fuera de un pedido web (aviso de
# desvíos, US 8.2). En Render, si no se define, se usa la URL pública que Render da al servicio.
AQUALAB_URL_BASE = (
    os.environ.get("AQUALAB_URL_BASE")
    or os.environ.get("RENDER_EXTERNAL_URL")
    or "http://localhost:8000"
)

# Asistente de consultas (US 10.1). Groq por defecto (API compatible con OpenAI, plan gratuito para
# la demo): alcanza con la clave en `.env`. Sin `ASISTENTE_API_KEY`, AquaLab funciona igual y el
# asistente aparece deshabilitado. Los tests nunca llaman al servicio.
ASISTENTE = {
    "clave": os.environ.get("ASISTENTE_API_KEY", ""),
    "url": os.environ.get("ASISTENTE_URL", "https://api.groq.com/openai/v1/chat/completions"),
    "modelo": os.environ.get("ASISTENTE_MODELO", "openai/gpt-oss-120b"),
}
