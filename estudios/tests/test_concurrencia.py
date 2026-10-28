import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection, transaction

from estudios.models import Estudio, TipoEstudio
from estudios.servicios import CrearEstudioError, VersionDesactualizada, crear_estudio

pytestmark = pytest.mark.django_db(transaction=True)


def ejecutar(datos, usuario_id, barrera=None):
    close_old_connections()
    try:
        usuario = get_user_model().objects.get(pk=usuario_id)
        if barrera:
            barrera.wait(timeout=10)
        return crear_estudio(datos, usuario).pk
    finally:
        connection.close()


@pytest.mark.parametrize("misma", [True, False])
def test_confirmaciones_simultaneas(datos, empleado, misma):
    barrera = threading.Barrier(2)
    otro = dict(datos) if misma else {**datos, "clave": str(uuid.uuid4())}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(ejecutar, d, empleado.pk, barrera) for d in [datos, otro]]
        ids = [f.result(timeout=15) for f in futuros]
    assert len(set(ids)) == (1 if misma else 2)
    assert Estudio.objects.count() == (1 if misma else 2)
    assert all(e.pruebas_asignadas.count() == 2 for e in Estudio.objects.all())


@pytest.mark.parametrize("desactivar", [False, True])
def test_editor_gana(datos, empleado, tipo, desactivar):
    # La confirmación empieza mientras otro escritor mantiene el lock del tipo.
    iniciado = threading.Event()

    def confirmar():
        iniciado.set()
        return ejecutar(datos, empleado.pk)

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            t = TipoEstudio.objects.select_for_update().get(pk=tipo.pk)
            futuro = pool.submit(confirmar)
            assert iniciado.wait(timeout=10)
            t.version += 1
            if desactivar:
                t.activo = False
            else:
                t.nombre = "Cambio concurrente"
                t.pruebas.set([t.pruebas.first()])
            t.save()
        with pytest.raises(CrearEstudioError if desactivar else VersionDesactualizada):
            futuro.result(timeout=15)
    assert not Estudio.objects.exists()


def test_creador_gana(datos, empleado, tipo, monkeypatch):
    from estudios import servicios

    entro = threading.Event()
    liberar = threading.Event()
    original = servicios.configuracion_bloqueada

    def configuracion(t):
        result = original(t)
        entro.set()
        assert liberar.wait(timeout=10)
        return result

    monkeypatch.setattr(servicios, "configuracion_bloqueada", configuracion)

    def editar():
        close_old_connections()
        try:
            with transaction.atomic():
                t = TipoEstudio.objects.select_for_update().get(pk=tipo.pk)
                t.nombre = "Nombre nuevo"
                t.version += 1
                t.pruebas.set([t.pruebas.first()])
                t.save()
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        creado = pool.submit(ejecutar, datos, empleado.pk)
        assert entro.wait(timeout=10)
        editor = pool.submit(editar)
        liberar.set()
        pk = creado.result(timeout=15)
        editor.result(timeout=15)
    e = Estudio.objects.get(pk=pk)
    assert e.tipo_nombre_snapshot == "Tipo de test" and e.pruebas_asignadas.count() == 2
    tipo.refresh_from_db()
    assert tipo.version == 2 and tipo.pruebas.count() == 1


@pytest.fixture(autouse=True)
def requiere_postgresql():
    assert connection.vendor == "postgresql", "Estos tests requieren PostgreSQL real."
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), version()")
        base, motor = cursor.fetchone()
    assert base.startswith("test_") and "PostgreSQL" in motor
