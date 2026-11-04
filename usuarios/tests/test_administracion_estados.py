import pytest
from django.urls import reverse

from .test_administracion_solicitudes import resolver

pytestmark = pytest.mark.django_db


def test_suspension_conserva_historia_y_reactiva_sin_aviso(
    cliente_panel,
    usuario_aprobado,
    historial_usuario,
    otros_privilegios,
    django_capture_on_commit_callbacks,
    mailoutbox,
):
    from django.test import Client

    from .conftest import PASSWORD_EXISTENTE

    usuario = usuario_aprobado
    referencia = historial_usuario(usuario, "muestra")
    firma = historial_usuario(usuario, "firma")
    grupo, permiso = otros_privilegios
    usuario.groups.add(grupo)
    usuario.user_permissions.add(permiso)
    sesion = Client()
    sesion.force_login(usuario)
    with django_capture_on_commit_callbacks(execute=True):
        resolver(cliente_panel, "desactivar", usuario)
        assert sesion.get(reverse("inicio")).status_code == 302
        resolver(cliente_panel, "reactivar", usuario)
    usuario.refresh_from_db()
    referencia.refresh_from_db()
    firma.refresh_from_db()
    assert usuario.aprobada and usuario.is_active
    assert usuario.groups.filter(pk=grupo.pk).exists()
    assert usuario.user_permissions.filter(pk=permiso.pk).exists()
    assert sesion.login(email=usuario.email, password=PASSWORD_EXISTENTE)
    assert not mailoutbox


def test_pendientes_y_propia_no_gestionables(cliente_panel, usuario_pendiente, administrador_panel):
    for nombre in ["cambiar_rol", "desactivar", "reactivar"]:
        respuesta = cliente_panel.get(
            reverse("administracion:" + nombre, args=[usuario_pendiente.pk]), follow=True
        )
        assert "Solicitudes" in respuesta.content.decode()
    respuesta = cliente_panel.get(
        reverse("administracion:desactivar", args=[administrador_panel.pk]), follow=True
    )
    assert "propia cuenta" in respuesta.content.decode()
    administrador_panel.refresh_from_db()
    assert administrador_panel.is_active


def test_cancelar_estado(cliente_panel, usuario_aprobado, mailoutbox):
    resolver(cliente_panel, "desactivar", usuario_aprobado, accion="cancelar")
    usuario_aprobado.refresh_from_db()
    assert usuario_aprobado.is_active and usuario_aprobado.version_administrativa == 1
    assert not mailoutbox
