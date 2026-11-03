"""Contención real PostgreSQL con conexiones independientes y espera comprobada."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import close_old_connections, connection, connections, transaction

from usuarios.models import Usuario
from usuarios.servicios_administracion import (
    GestionUsuarioError,
    bloquear,
    cambiar_estado_panel,
    cambiar_rol_panel,
    guardar_cuenta_admin,
    instantanea,
    resolver_panel,
    resolver_solicitudes_admin,
)

from .test_administracion_servicios import peticion

pytestmark = pytest.mark.django_db(transaction=True)


def ejecutar_hilo(funcion, listo, pid):
    close_old_connections()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET lock_timeout = '5s'")
            cursor.execute("SET statement_timeout = '8s'")
            cursor.execute("SELECT pg_backend_pid()")
            pid.append(cursor.fetchone()[0])
        listo.set()
        try:
            return funcion()
        except GestionUsuarioError as exc:
            return exc
    finally:
        connections.close_all()


def carrera(request, objetivo, primero, segundo):
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    listo, pid = threading.Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with bloquear(request, [objetivo.pk]):
            futuro = pool.submit(ejecutar_hilo, segundo, listo, pid)
            assert listo.wait(5)
            limite = time.monotonic() + 5
            while time.monotonic() < limite:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT cardinality(pg_blocking_pids(%s))", [pid[0]])
                    esperando = cursor.fetchone()[0] > 0
                if esperando:
                    break
                threading.Event().wait(0.01)
            assert esperando, "El competidor debe esperar un bloqueo PostgreSQL real"
            uno = primero()
        dos = futuro.result(timeout=10)
    return uno, dos


@pytest.mark.parametrize(
    "primera,segunda",
    [
        ("aprobar", "aprobar"),
        ("aprobar", "rechazar"),
        ("rechazar", "aprobar"),
        ("rechazar", "rechazar"),
    ],
)
def test_una_resolucion_y_un_aviso(
    administrador_panel, usuario_pendiente, mailoutbox, primera, segunda
):
    request = peticion(administrador_panel)
    uno, dos = carrera(
        request,
        usuario_pendiente,
        lambda: resolver_panel(request, usuario_pendiente.pk, primera, 1),
        lambda: resolver_panel(request, usuario_pendiente.pk, segunda, 1),
    )
    assert uno is True
    assert isinstance(dos, GestionUsuarioError)
    assert len(mailoutbox) == 1
    assert Usuario.objects.filter(pk=usuario_pendiente.pk, aprobada=True).exists() == (
        primera == "aprobar"
    )


@pytest.mark.parametrize("via", ["accion", "ficha"])
def test_panel_frente_admin(administrador_panel, administrador, usuario_pendiente, mailoutbox, via):
    request, admin = peticion(administrador_panel), peticion(administrador)
    original = instantanea(usuario_pendiente)
    usuario_pendiente.is_active = True

    def competidor():
        if via == "accion":
            return resolver_solicitudes_admin(admin, [usuario_pendiente.pk], "aprobar")
        return guardar_cuenta_admin(admin, usuario_pendiente, 1, original, ["is_active"])

    uno, dos = carrera(
        request,
        usuario_pendiente,
        lambda: resolver_panel(request, usuario_pendiente.pk, "aprobar", 1),
        competidor,
    )
    assert uno is True
    assert dos == (0, []) if via == "accion" else isinstance(dos, GestionUsuarioError)
    assert len(mailoutbox) == 1
    vigente = Usuario.objects.get(pk=usuario_pendiente.pk)
    assert vigente.aprobada and vigente.is_active and vigente.version_administrativa == 2


def test_aviso_solo_tras_commit_real(
    administrador_panel, usuario_pendiente, monkeypatch, mailoutbox
):
    from usuarios import notificaciones

    original = notificaciones.avisar_aprobacion
    llamadas = []

    def avisar(request, usuario):
        llamadas.append(connection.in_atomic_block)
        original(request, usuario)

    monkeypatch.setattr(notificaciones, "avisar_aprobacion", avisar)
    with transaction.atomic():
        resolver_panel(peticion(administrador_panel), usuario_pendiente.pk, "aprobar", 1)
        assert llamadas == []
        assert mailoutbox == []
    assert llamadas == [False]
    assert len(mailoutbox) == 1


def test_rol_frente_estado(administrador_panel, usuario_aprobado, grupo_bioquimicos):
    request = peticion(administrador_panel)
    uno, dos = carrera(
        request,
        usuario_aprobado,
        lambda: cambiar_rol_panel(request, usuario_aprobado.pk, True, 1),
        lambda: cambiar_estado_panel(request, usuario_aprobado.pk, False, 1),
    )
    assert uno is True and isinstance(dos, GestionUsuarioError)
    usuario_aprobado.refresh_from_db()
    assert usuario_aprobado.is_active and usuario_aprobado.version_administrativa == 2


def test_objetivos_cruzados_sin_deadlock(
    administrador_panel, grupo_administradores, grupo_bioquimicos, django_user_model
):
    otro = django_user_model.objects.create_user(email="cruzado@lab.com")
    otro.groups.add(grupo_administradores)
    barrera = threading.Barrier(2)

    def ejecutar(actor, objetivo):
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '5s'")
            barrera.wait(timeout=5)
            return cambiar_rol_panel(peticion(actor), objetivo.pk, True, 1)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(ejecutar, administrador_panel, otro)
        b = pool.submit(ejecutar, otro, administrador_panel)
        assert a.result(timeout=10) and b.result(timeout=10)
