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


def test_cuenta_registrada_y_aprobada_autentica(client, datos_registro, password_registro):
    client.post(reverse("usuarios:registro"), datos_registro)
    client.post(reverse("usuarios:registro_confirmar"), {"accion": "confirmar"})

    usuario = get_user_model().objects.get(email="ana@lab.com")
    assert authenticate(email="ana@lab.com", password=password_registro) is None

    usuario.is_active = True
    usuario.save()

    assert authenticate(email="ana@lab.com", password=password_registro) == usuario
