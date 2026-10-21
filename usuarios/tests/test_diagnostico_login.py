from unittest.mock import patch

import pytest
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import PBKDF2PasswordHasher, check_password
from django.db import DatabaseError
from django.urls import reverse

from .conftest import PASSWORD_EXISTENTE

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("cuenta", ["inexistente", "usuario_aprobado", "usuario_pendiente"])
def test_diagnostico_uniforme(client, request, cuenta):
    from usuarios import forms

    email = "ausente@lab.com" if cuenta == "inexistente" else request.getfixturevalue(cuenta).email
    with (
        patch("django.contrib.auth.forms.authenticate", wraps=authenticate) as auth,
        patch.object(forms, "check_password", wraps=check_password) as diagnostico,
        patch.object(
            get_user_model()._default_manager,
            "get_by_natural_key",
            wraps=get_user_model()._default_manager.get_by_natural_key,
        ) as consulta,
        patch.object(
            PBKDF2PasswordHasher, "encode", autospec=True, side_effect=PBKDF2PasswordHasher.encode
        ) as encode,
    ):
        respuesta = client.post(reverse("usuarios:login"), {"username": email, "password": "mal"})
    assert respuesta.status_code == 200
    assert auth.call_count == 1
    # La primera consulta pertenece al backend; la segunda, al diagnóstico.
    assert consulta.call_count == 2
    assert consulta.call_args_list[0] == consulta.call_args_list[1]
    assert diagnostico.call_count == 1
    assert encode.call_count == 2
    assert "setter" not in diagnostico.call_args.kwargs


def test_exito_no_diagnostica(client, usuario_aprobado):
    with patch("usuarios.forms.check_password") as diagnostico:
        respuesta = client.post(
            reverse("usuarios:login"),
            {
                "username": usuario_aprobado.email,
                "password": PASSWORD_EXISTENTE,
            },
        )
    assert respuesta.status_code == 302
    diagnostico.assert_not_called()


@pytest.mark.parametrize("hash_password", ["!inutilizable", "hash-no-reconocido"])
def test_hash_no_utilizable_generico(client, usuario_pendiente, hash_password):
    usuario_pendiente.password = hash_password
    usuario_pendiente.save()
    respuesta = client.post(
        reverse("usuarios:login"),
        {
            "username": usuario_pendiente.email,
            "password": PASSWORD_EXISTENTE,
        },
    )
    assert "Usuario o contraseña incorrectos" in respuesta.content.decode()
    assert "_auth_user_id" not in client.session


def test_hash_antiguo_compensa_sin_actualizacion_diagnostica(client, usuario_pendiente):
    hasher = PBKDF2PasswordHasher()
    usuario_pendiente.password = hasher.encode(PASSWORD_EXISTENTE, hasher.salt(), iterations=1000)
    usuario_pendiente.save()
    anterior = usuario_pendiente.password
    with patch.object(
        PBKDF2PasswordHasher,
        "harden_runtime",
        autospec=True,
        side_effect=PBKDF2PasswordHasher.harden_runtime,
    ) as harden:
        respuesta = client.post(
            reverse("usuarios:login"),
            {
                "username": usuario_pendiente.email,
                "password": "incorrecta",
            },
        )
    usuario_pendiente.refresh_from_db()
    assert respuesta.status_code == 200
    assert harden.call_count == 2
    assert usuario_pendiente.password == anterior


@pytest.mark.parametrize(
    "punto", ["django.contrib.auth.forms.authenticate", "usuarios.forms.check_password"]
)
def test_error_operativo_no_filtra(client, usuario_pendiente, punto, caplog):
    with patch(punto, side_effect=DatabaseError("SQL SECRETO")):
        respuesta = client.post(
            reverse("usuarios:login"),
            {
                "username": usuario_pendiente.email,
                "password": PASSWORD_EXISTENTE,
            },
        )
    assert respuesta.status_code == 200
    assert "No se pudo iniciar sesión" in respuesta.content.decode()
    assert "SQL SECRETO" not in respuesta.content.decode() + caplog.text
    assert PASSWORD_EXISTENTE not in respuesta.content.decode() + caplog.text
    assert "_auth_user_id" not in client.session


def test_fallo_consulta_diagnostica_no_filtra(client, usuario_pendiente):
    manager = get_user_model()._default_manager
    original = manager.get_by_natural_key
    llamadas = 0

    def consultar(email):
        nonlocal llamadas
        llamadas += 1
        if llamadas == 2:
            raise DatabaseError("SQL SECRETO")
        return original(email)

    with patch.object(manager, "get_by_natural_key", side_effect=consultar):
        respuesta = client.post(
            reverse("usuarios:login"),
            {
                "username": usuario_pendiente.email,
                "password": PASSWORD_EXISTENTE,
            },
        )
    assert respuesta.status_code == 200
    assert "No se pudo iniciar sesión" in respuesta.content.decode()
    assert "SQL SECRETO" not in respuesta.content.decode()
    assert respuesta.context["form"].get_user() is None
    assert "_auth_user_id" not in client.session
