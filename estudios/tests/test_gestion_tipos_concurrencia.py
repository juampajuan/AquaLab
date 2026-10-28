import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import close_old_connections, connection, connections, transaction

from estudios.gestion_tipos import (
    DatosTipoInvalidos,
    TipoUtilizado,
    VersionTipoDesactualizada,
    gestionar_tipo_estudio,
)
from estudios.models import Estudio, TipoEstudio
from estudios.servicios import CrearEstudioError, VersionDesactualizada, crear_estudio

"""Carreras con locks reales PostgreSQL; sin mocks de select_for_update."""


pytestmark = pytest.mark.django_db(transaction=True)


def en_hilo(funcion):
    close_old_connections()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET lock_timeout = '5s'")
            cursor.execute("SET statement_timeout = '8s'")
        return funcion()
    except Exception as exc:
        return exc
    finally:
        connections.close_all()


def carrera_ordenada(tipo, primero, segundo):
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    listo = threading.Event()
    pid = []

    def competidor():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_backend_pid()")
            pid.append(cursor.fetchone()[0])
        listo.set()
        return segundo()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            TipoEstudio.objects.select_for_update().get(pk=tipo.pk)
            future = pool.submit(en_hilo, competidor)
            assert listo.wait(5)
            limite = time.monotonic() + 5
            bloqueado = False
            while time.monotonic() < limite:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT cardinality(pg_blocking_pids(%s))", [pid[0]])
                    bloqueado = cursor.fetchone()[0] > 0
                if bloqueado:
                    break
                threading.Event().wait(0.01)
            assert bloqueado, "El competidor debe esperar un lock PostgreSQL real"
            try:
                resultado = primero()
            except Exception as exc:
                resultado = exc
        otro = future.result(timeout=10)
    return resultado, otro


def edicion(gestor, tipo, nombre="Administrado"):
    return gestionar_tipo_estudio(
        usuario=gestor,
        operacion="editar",
        tipo_id=tipo.pk,
        version_esperada=1,
        datos={"nombre": nombre, "descripcion": "Nueva", "prueba_ids": [tipo.pruebas.first().pk]},
    )


def test_dos_editores(gestor, tipo):
    uno, dos = carrera_ordenada(
        tipo, lambda: edicion(gestor, tipo), lambda: edicion(gestor, tipo, "Otro")
    )
    assert uno.version_final == 2
    assert isinstance(dos, VersionTipoDesactualizada)
    tipo.refresh_from_db()
    assert (tipo.nombre, tipo.version) == ("Administrado", 2)


@pytest.mark.parametrize("admin_primero", [True, False])
def test_edicion_con_creacion(gestor, tipo, empleado, datos, admin_primero):
    def admin():
        return edicion(gestor, tipo)

    def crear():
        return crear_estudio(datos, empleado)

    a, b = carrera_ordenada(
        tipo, admin if admin_primero else crear, crear if admin_primero else admin
    )
    if admin_primero:
        assert isinstance(b, VersionDesactualizada)
        assert not Estudio.objects.exists()
    else:
        assert isinstance(a, Estudio)
        assert a.tipo_nombre_snapshot == "Tipo de test"
        assert a.pruebas_asignadas.count() == 2
        assert b.version_final == 2


def test_altas_nombre_equivalente(gestor, pruebas):
    assert connection.vendor == "postgresql"
    barrier = threading.Barrier(2)

    def crear(nombre):
        barrier.wait(timeout=5)
        return gestionar_tipo_estudio(
            usuario=gestor,
            operacion="crear",
            datos={"nombre": nombre, "descripcion": "", "prueba_ids": [pruebas[0].pk]},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [
            pool.submit(en_hilo, lambda n=n: crear(n)) for n in ["DEMO carrera", "demo CARRERA"]
        ]
        resultados = [f.result(timeout=15) for f in futuros]
    assert sum(isinstance(r, DatosTipoInvalidos) for r in resultados) == 1
    assert TipoEstudio.objects.count() == 1


@pytest.mark.parametrize("operacion", ["desactivar", "eliminar", "reactivar"])
@pytest.mark.parametrize("admin_primero", [True, False])
def test_disponibilidad_eliminacion_con_creacion(
    gestor, tipo, datos, empleado, operacion, admin_primero
):
    if operacion == "reactivar":
        tipo.activo = False
        tipo.save()

    def admin():
        return gestionar_tipo_estudio(
            usuario=gestor, operacion=operacion, tipo_id=tipo.pk, version_esperada=1
        )

    def crear():
        return crear_estudio(datos, empleado)

    # Reactivación: versión antigua nunca acepta una configuración nueva; creación previa rechaza.
    a, b = carrera_ordenada(
        tipo, admin if admin_primero else crear, crear if admin_primero else admin
    )
    if admin_primero:
        assert isinstance(b, CrearEstudioError)
        assert not Estudio.objects.exists()
    elif operacion == "reactivar":
        assert isinstance(a, CrearEstudioError)
        assert b.estado == "reactivado"
        assert not Estudio.objects.exists()
    elif operacion == "eliminar":
        assert isinstance(a, Estudio)
        assert isinstance(b, TipoUtilizado)
        assert TipoEstudio.objects.filter(pk=tipo.pk).exists()
    else:
        assert isinstance(a, Estudio)
        assert b.estado == "desactivado"
        assert a.pruebas_asignadas.count() == 2


def test_dos_operaciones_misma_version(gestor, tipo):
    a, b = carrera_ordenada(
        tipo,
        lambda: gestionar_tipo_estudio(
            usuario=gestor, operacion="desactivar", tipo_id=tipo.pk, version_esperada=1
        ),
        lambda: gestionar_tipo_estudio(
            usuario=gestor, operacion="eliminar", tipo_id=tipo.pk, version_esperada=1
        ),
    )
    assert a.estado == "desactivado"
    assert isinstance(b, VersionTipoDesactualizada)
    assert TipoEstudio.objects.filter(pk=tipo.pk).exists()


def test_editores_distintos_nombre_equivalente(gestor, otro_gestor, tipo, pruebas):
    otro = TipoEstudio.objects.create(nombre="Otro tipo")
    otro.pruebas.set(pruebas)
    barrier = threading.Barrier(2)

    def editar(usuario, pk, nombre):
        barrier.wait(timeout=5)
        return gestionar_tipo_estudio(
            usuario=usuario,
            operacion="editar",
            tipo_id=pk,
            version_esperada=1,
            datos={"nombre": nombre, "descripcion": "", "prueba_ids": [pruebas[0].pk]},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [
            pool.submit(en_hilo, lambda: editar(gestor, tipo.pk, "Mismo nombre")),
            pool.submit(en_hilo, lambda: editar(otro_gestor, otro.pk, "MISMO NOMBRE")),
        ]
        resultados = [f.result(timeout=15) for f in futuros]
    assert sum(isinstance(r, DatosTipoInvalidos) for r in resultados) == 1
    assert sorted(TipoEstudio.objects.values_list("version", flat=True)) == [1, 2]
