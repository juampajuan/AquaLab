"""Integración mínima del nuevo estado con los caminos existentes, sin panel nuevo."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from .conftest import PASSWORD_EXISTENTE
from .test_notificaciones import aplicar_accion, datos_ficha

pytestmark = pytest.mark.django_db


def test_accion_aprobar_no_reactiva_desactivada(
    cliente_admin, usuario_desactivado, django_capture_on_commit_callbacks, mailoutbox
):
    with django_capture_on_commit_callbacks(execute=True):
        respuesta = aplicar_accion(cliente_admin, "aprobar_cuentas", [usuario_desactivado])
    assert respuesta.status_code == 200
    usuario_desactivado.refresh_from_db()
    assert usuario_desactivado.estado_cuenta == "desactivada"
    assert usuario_desactivado.version_administrativa == 1
    assert mailoutbox == []


def test_accion_rechazar_no_elimina_desactivada(
    cliente_admin, usuario_desactivado, django_capture_on_commit_callbacks, mailoutbox
):
    with django_capture_on_commit_callbacks(execute=True):
        aplicar_accion(cliente_admin, "rechazar_solicitudes", [usuario_desactivado], confirmar="si")
    assert get_user_model().objects.filter(pk=usuario_desactivado.pk).exists()
    usuario_desactivado.refresh_from_db()
    assert usuario_desactivado.estado_cuenta == "desactivada"
    assert mailoutbox == []


@pytest.mark.parametrize("cuenta", ["usuario_pendiente", "usuario_desactivado"])
def test_ficha_activa_coherentemente_y_solo_aprobar_avisa(
    request, cuenta, cliente_admin, django_capture_on_commit_callbacks, mailoutbox
):
    usuario = request.getfixturevalue(cuenta)
    with django_capture_on_commit_callbacks(execute=True):
        respuesta = cliente_admin.post(
            reverse("admin:usuarios_usuario_change", args=[usuario.pk]),
            datos_ficha(cliente_admin, usuario, is_active="on"),
        )
    assert respuesta.status_code == 302
    usuario.refresh_from_db()
    assert usuario.estado_cuenta == "activa"
    assert usuario.version_administrativa == 2
    assert len(mailoutbox) == (1 if cuenta == "usuario_pendiente" else 0)


def test_accion_aprobar_marca_aprobacion_y_version(
    cliente_admin, usuario_pendiente, django_capture_on_commit_callbacks, mailoutbox
):
    with django_capture_on_commit_callbacks(execute=True):
        aplicar_accion(cliente_admin, "aprobar_cuentas", [usuario_pendiente])
    usuario_pendiente.refresh_from_db()
    assert usuario_pendiente.aprobada and usuario_pendiente.is_active
    assert usuario_pendiente.version_administrativa == 2
    assert len(mailoutbox) == 1


@pytest.mark.parametrize("clave_correcta", [True, False])
def test_login_diferencia_suspension_solo_con_clave_correcta(
    client, usuario_desactivado, clave_correcta
):
    respuesta = client.post(
        reverse("usuarios:login"),
        {
            "username": usuario_desactivado.email,
            "password": PASSWORD_EXISTENTE if clave_correcta else "clave-incorrecta",
        },
    )
    assert respuesta.status_code == 200
    texto = respuesta.content.decode()
    assert "pendiente de aprobación" not in texto
    if clave_correcta:
        assert "Tu cuenta está desactivada" in texto
    else:
        assert "Usuario o contraseña incorrectos" in texto
        assert "Tu cuenta está desactivada" not in texto
    assert "_auth_user_id" not in client.session
