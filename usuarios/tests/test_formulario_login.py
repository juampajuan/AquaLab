from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from .conftest import PASSWORD_EXISTENTE

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("datos", [{}, {"username": "a@b.com"}, {"password": "clave"}])
def test_incompleto_no_autentica(client, datos):
    with patch("django.contrib.auth.forms.authenticate") as autenticar:
        respuesta = client.post(reverse("usuarios:login"), datos)
    assert respuesta.status_code == 200
    autenticar.assert_not_called()
    assert "_auth_user_id" not in client.session


@pytest.mark.parametrize("cuenta", ["inexistente", "usuario_aprobado", "usuario_pendiente"])
def test_error_generico(client, request, cuenta):
    email = "ausente@lab.com" if cuenta == "inexistente" else request.getfixturevalue(cuenta).email
    respuesta = client.post(
        reverse("usuarios:login"),
        {
            "username": email,
            "password": "incorrecta",
        },
    )
    form = respuesta.context["form"]
    assert respuesta.status_code == 200
    assert list(form.non_field_errors()) == ["Usuario o contraseña incorrectos"]
    assert form.errors.as_data()["__all__"][0].code == "invalid_login"
    assert form.get_user() is None
    assert "_auth_user_id" not in client.session


def test_pendiente_no_ingresa(client, usuario_pendiente):
    respuesta = client.post(
        reverse("usuarios:login"),
        {
            "username": usuario_pendiente.email,
            "password": PASSWORD_EXISTENTE,
        },
    )
    assert respuesta.status_code == 200
    assert "Tu cuenta está pendiente de aprobación" in respuesta.content.decode()
    assert respuesta.context["form"].get_user() is None
    assert "_auth_user_id" not in client.session


def test_correo_normalizado_password_literal(client, usuario_aprobado):
    usuario_aprobado.set_password("  Clave-con-espacios-987  ")
    usuario_aprobado.save()
    for password, estado in [("Clave-con-espacios-987", 200), ("  Clave-con-espacios-987  ", 302)]:
        respuesta = client.post(
            reverse("usuarios:login"),
            {
                "username": "  " + usuario_aprobado.email.upper() + "  ",
                "password": password,
            },
        )
        assert respuesta.status_code == estado


def test_unicode_registro_aprobacion_login(client, datos_registro):
    email = "ANA@ｅxample.com"
    datos = {**datos_registro, "email": email}
    client.post(reverse("usuarios:registro"), datos)
    client.post(reverse("usuarios:registro_confirmar"), {"accion": "confirmar"})
    usuario = get_user_model().objects.get(email="ana@ｅxample.com")
    usuario.is_active = True
    usuario.save()
    respuesta = client.post(
        reverse("usuarios:login"),
        {
            "username": "  " + email + "  ",
            "password": datos["password1"],
        },
    )
    assert respuesta.status_code == 302
    assert client.session["_auth_user_id"] == str(usuario.pk)


def test_fallo_conserva_borrador(client):
    sesion = client.session
    sesion["registro_pendiente"] = {"email": "borrador@lab.com"}
    sesion.save()
    client.post(reverse("usuarios:login"), {"username": "ausente@lab.com", "password": "mal"})
    assert client.session["registro_pendiente"]["email"] == "borrador@lab.com"
