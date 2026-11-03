"""Reglas compartidas de resolución y edición; no requieren pantallas del panel."""

from types import SimpleNamespace

import pytest
from django.core.exceptions import PermissionDenied
from django.db import transaction

from usuarios.models import Usuario
from usuarios.servicios_administracion import (
    GestionUsuarioError,
    cambiar_estado_panel,
    cambiar_rol_panel,
    resolver_panel,
    resolver_solicitudes_admin,
)

pytestmark = pytest.mark.django_db


def peticion(actor):
    return SimpleNamespace(user=actor, build_absolute_uri=lambda url: "http://testserver" + url)


def test_aprobacion_unica_y_reactivacion_sin_aviso(
    administrador_panel, usuario_pendiente, django_capture_on_commit_callbacks, mailoutbox
):
    request = peticion(administrador_panel)
    with django_capture_on_commit_callbacks(execute=True):
        assert resolver_panel(request, usuario_pendiente.pk, "aprobar", 1)
        assert not resolver_panel(request, usuario_pendiente.pk, "aprobar", 2)
    assert len(mailoutbox) == 1
    cambiar_estado_panel(request, usuario_pendiente.pk, False, 2)
    with django_capture_on_commit_callbacks(execute=True):
        cambiar_estado_panel(request, usuario_pendiente.pk, True, 3)
    usuario_pendiente.refresh_from_db()
    assert usuario_pendiente.aprobada and usuario_pendiente.is_active
    assert usuario_pendiente.version_administrativa == 4
    assert len(mailoutbox) == 1


def test_rechazo_libera_correo_y_rollback_no_avisa(
    administrador_panel, usuario_pendiente, django_capture_on_commit_callbacks, mailoutbox
):
    request = peticion(administrador_panel)
    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(RuntimeError), transaction.atomic():
            resolver_panel(request, usuario_pendiente.pk, "rechazar", 1)
            raise RuntimeError("rollback")
    assert Usuario.objects.filter(pk=usuario_pendiente.pk).exists()
    assert not mailoutbox
    with django_capture_on_commit_callbacks(execute=True):
        resolver_panel(request, usuario_pendiente.pk, "rechazar", 1)
    assert not Usuario.objects.filter(email=usuario_pendiente.email).exists()
    assert len(mailoutbox) == 1


@pytest.mark.parametrize("relacion", ["firma", "muestra"])
def test_rechazo_impedido_y_aprobacion_posterior(
    administrador_panel,
    usuario_pendiente,
    historial_usuario,
    relacion,
    django_capture_on_commit_callbacks,
    mailoutbox,
):
    referencia = historial_usuario(usuario_pendiente, relacion)
    request = peticion(administrador_panel)
    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(GestionUsuarioError, match="historial|firma"):
            resolver_panel(request, usuario_pendiente.pk, "rechazar", 1)
    usuario_pendiente.refresh_from_db()
    assert not usuario_pendiente.aprobada and not usuario_pendiente.is_active
    assert usuario_pendiente.version_administrativa == 1
    assert not mailoutbox
    referencia.refresh_from_db()
    with django_capture_on_commit_callbacks(execute=True):
        resolver_panel(request, usuario_pendiente.pk, "aprobar", 1)
    referencia.refresh_from_db()
    assert len(mailoutbox) == 1


def test_autorizacion_estado_y_revision(administrador_panel, usuario_pendiente, usuario_aprobado):
    with pytest.raises(PermissionDenied):
        resolver_panel(peticion(usuario_aprobado), usuario_pendiente.pk, "aprobar", 1)
    request = peticion(administrador_panel)
    with pytest.raises(GestionUsuarioError):
        cambiar_estado_panel(request, administrador_panel.pk, False, 1)
    with pytest.raises(GestionUsuarioError):
        cambiar_estado_panel(request, usuario_pendiente.pk, True, 1)
    cambiar_estado_panel(request, usuario_aprobado.pk, False, 1)
    cambiar_estado_panel(request, usuario_aprobado.pk, True, 2)
    with pytest.raises(GestionUsuarioError, match="cambió"):
        cambiar_estado_panel(request, usuario_aprobado.pk, False, 1)


def test_rol_propio_preserva_otros_grupos_y_permisos(administrador_panel, grupo_bioquimicos):
    request = peticion(administrador_panel)
    originales = set(administrador_panel.groups.values_list("pk", flat=True))
    cambiar_rol_panel(request, administrador_panel.pk, True, 1)
    assert set(administrador_panel.groups.values_list("pk", flat=True)) == originales | {
        grupo_bioquimicos.pk
    }
    cambiar_rol_panel(request, administrador_panel.pk, False, 2)
    assert set(administrador_panel.groups.values_list("pk", flat=True)) == originales


def test_adaptadores_admin_conservan_autorizacion_independiente(
    administrador,
    administrador_panel,
    usuario_pendiente,
    django_capture_on_commit_callbacks,
    mailoutbox,
):
    with pytest.raises(PermissionDenied):
        resolver_solicitudes_admin(peticion(administrador_panel), [usuario_pendiente.pk], "aprobar")
    with pytest.raises(PermissionDenied):
        resolver_panel(peticion(administrador), usuario_pendiente.pk, "aprobar", 1)
    with django_capture_on_commit_callbacks(execute=True):
        assert resolver_solicitudes_admin(
            peticion(administrador), [usuario_pendiente.pk], "aprobar"
        ) == (1, [])
    assert len(mailoutbox) == 1


def test_servicio_reautoriza_actor_revocado(administrador_panel, usuario_pendiente):
    request = peticion(administrador_panel)
    # La instancia del request conserva is_active viejo deliberadamente.
    Usuario.objects.filter(pk=administrador_panel.pk).update(is_active=False)
    with pytest.raises(PermissionDenied):
        resolver_panel(request, usuario_pendiente.pk, "aprobar", 1)
    usuario_pendiente.refresh_from_db()
    assert not usuario_pendiente.aprobada
