import pytest
from django.contrib.auth import authenticate, get_user_model
from django.urls import reverse

from .conftest import PASSWORD_EXISTENTE

pytestmark = pytest.mark.django_db


def test_cuenta_pendiente_no_autentica(client, usuario_pendiente):
    assert authenticate(email=usuario_pendiente.email, password=PASSWORD_EXISTENTE) is None
    assert client.login(email=usuario_pendiente.email, password=PASSWORD_EXISTENTE) is False


def test_cuenta_aprobada_autentica(client, usuario_aprobado):
    assert (
        authenticate(email=usuario_aprobado.email, password=PASSWORD_EXISTENTE) == usuario_aprobado
    )
    assert client.login(email=usuario_aprobado.email, password=PASSWORD_EXISTENTE) is True


def test_cuenta_registrada_y_aprobada_autentica(
    client, cliente_admin, datos_registro, password_registro
):
    client.post(reverse("usuarios:registro"), datos_registro)
    client.post(reverse("usuarios:registro_confirmar"), {"accion": "confirmar"})

    usuario = get_user_model().objects.get(email="ana@lab.com")
    assert authenticate(email="ana@lab.com", password=password_registro) is None

    cliente_admin.post(
        reverse("admin:usuarios_usuario_changelist"),
        {"action": "aprobar_cuentas", "_selected_action": [usuario.pk]},
    )
    usuario.refresh_from_db()
    assert usuario.aprobada and usuario.is_active

    assert authenticate(email="ana@lab.com", password=password_registro) == usuario
