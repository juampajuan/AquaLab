#!/bin/sh
# Arranque del contenedor en producción (Render). Render gratis no tiene comando previo al deploy
# ni consola, así que las migraciones y la carga inicial van acá; todo es seguro de repetir porque
# el servicio se reinicia cada vez que despierta.
set -e

python manage.py migrate --noinput

# El catálogo se importa solo la primera vez: importar_catalogo_pruebas actualiza por código y
# pisaría los cambios hechos después desde la app (SCRUM-73).
if python manage.py shell --no-imports -c "import sys; from pruebas.models import Prueba; sys.exit(0 if Prueba.objects.exists() else 1)"; then
    echo "Catálogo de pruebas: ya cargado."
else
    python manage.py importar_catalogo_pruebas
fi

# Superusuario inicial desde DJANGO_SUPERUSER_EMAIL, _PASSWORD, _FIRST_NAME y _LAST_NAME. Solo al
# crearlo se lo suma a Administradores (el panel lo exige también al superusuario) y a Bioquímicos
# (validar y emitir); después los grupos se manejan desde la app y un reinicio no los repone.
if [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ]; then
    if python manage.py createsuperuser --noinput; then
        python manage.py shell --no-imports -c "import os; from django.contrib.auth.models import Group; from usuarios.models import Usuario; Usuario.objects.get(email=os.environ['DJANGO_SUPERUSER_EMAIL']).groups.add(*Group.objects.filter(name__in=['Administradores', 'Bioquímicos']))"
        echo "Superusuario creado en Administradores y Bioquímicos."
    else
        echo "Superusuario: no se creó (¿ya existe?)."
    fi
fi

# Historial del laboratorio para la presentación (estudios/historial.py): solo si está definida la
# contraseña de sus usuarios; no carga dos veces. Si falla, el sitio arranca igual.
if [ -n "${AQUALAB_HISTORIAL_CONTRASENA:-}" ]; then
    python manage.py cargar_historial || echo "Historial: no se pudo cargar."
fi

# Dos procesos con hilos: el asistente puede tardar hasta 20 s y el plan gratis tiene 512 MB.
exec gunicorn config.wsgi \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --threads 4 \
    --timeout 60 \
    --access-logfile -
