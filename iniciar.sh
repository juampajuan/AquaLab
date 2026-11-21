#!/bin/sh
# Arranque en Render (CMD del Dockerfile). En local se usa docker-compose.yml con runserver.
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Sitio de demostración: carga la demo una sola vez (si ya está, avisa y sigue).
if [ "$AQUALAB_ENTORNO" = "demo" ]; then
    python manage.py cargar_demo || echo "No se pudo cargar la demo; se sigue sin ella."
fi

exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 2 --timeout 120
