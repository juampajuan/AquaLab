import re

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.db import DatabaseError
from django.urls import reverse

from .conftest import PASSWORD_EXISTENTE

pytestmark = pytest.mark.django_db

CLAVE_SESION = "registro_pendiente"
MENSAJE_EXITO = "Registro recibido. Vas a poder ingresar cuando un administrador apruebe tu cuenta."
MENSAJE_NO_DISPONIBLE = "Este correo no está disponible."
AVISO_REVISION = (
    "Revisá tus datos. Al confirmar, tu cuenta quedará pendiente de aprobación por un "
    "administrador."
)


def cantidad_usuarios():
    return get_user_model().objects.count()


def input_de(html, nombre):
    encontrado = re.search(rf'<input[^>]*name="{nombre}"[^>]*>', html)
    assert encontrado, f"no se encontró el input {nombre}"
    return encontrado.group(0)


# Paso 1: formulario


def test_registro_accesible_sin_sesion(client):
    assert client.get(reverse("usuarios:registro")).status_code == 200
    assert client.get(reverse("usuarios:registro_recibido")).status_code == 200


@pytest.mark.parametrize(
    "campos_vacios",
    [
        ["first_name"],
        ["last_name"],
        ["email"],
        ["password1"],
        ["password2"],
        ["first_name", "last_name", "email", "password1", "password2"],
    ],
    ids=["first_name", "last_name", "email", "password1", "password2", "todos"],
)
def test_formulario_incompleto_no_avanza(client, datos_registro, campos_vacios):
    datos = {**datos_registro, **dict.fromkeys(campos_vacios, "")}

    respuesta = client.post(reverse("usuarios:registro"), datos)

    assert respuesta.status_code == 200
    errores = respuesta.context["form"].errors
    for campo in campos_vacios:
        assert "Este campo es obligatorio." in errores[campo]
    assert "Este campo es obligatorio." in respuesta.content.decode()
    assert CLAVE_SESION not in client.session
    assert cantidad_usuarios() == 0


@pytest.mark.parametrize("email", ["ana@", "ana.lab.com", "ana@@lab.com"])
def test_correo_invalido_rechazado(client, datos_registro, email):
    respuesta = client.post(reverse("usuarios:registro"), {**datos_registro, "email": email})

    assert respuesta.status_code == 200
    assert "Introduzca una dirección de email válida." in respuesta.context["form"].errors["email"]
    assert CLAVE_SESION not in client.session
    assert cantidad_usuarios() == 0

    confirmar = client.get(reverse("usuarios:registro_confirmar"))
    assert confirmar.status_code == 302
    assert confirmar.url == reverse("usuarios:registro")


@pytest.mark.parametrize("cuenta_activa", [False, True], ids=["pendiente", "aprobada"])
@pytest.mark.parametrize("email", ["ANA@lab.com", "  ana@lab.com  ", "Ana@Lab.Com"])
def test_correo_duplicado_rechazado(client, datos_registro, cuenta_activa, email):
    get_user_model().objects.create_user(
        email="ana@lab.com",
        password=PASSWORD_EXISTENTE,
        first_name="Ana",
        last_name="Existente",
        is_active=cuenta_activa,
    )

    respuesta = client.post(reverse("usuarios:registro"), {**datos_registro, "email": email})

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["email"] == [MENSAJE_NO_DISPONIBLE]
    assert respuesta.content.decode().count(MENSAJE_NO_DISPONIBLE) == 1
    assert CLAVE_SESION not in client.session
    assert cantidad_usuarios() == 1


@pytest.mark.parametrize(
    ("password1", "password2"),
    [
        ("Ab-12x", "Ab-12x"),
        ("83920571946", "83920571946"),
        ("password123", "password123"),
        ("Clave-Secreta-Unica-987", "Otra-Clave-Distinta-321"),
    ],
    ids=["corta", "solo_numeros", "comun", "distintas"],
)
def test_password_invalida_rechazada(client, datos_registro, password1, password2):
    datos = {**datos_registro, "password1": password1, "password2": password2}

    respuesta = client.post(reverse("usuarios:registro"), datos)

    assert respuesta.status_code == 200
    errores = respuesta.context["form"].errors
    assert errores.get("password1") or errores.get("password2")
    assert CLAVE_SESION not in client.session
    assert cantidad_usuarios() == 0


@pytest.mark.parametrize(
    ("cambios", "conserva_email"),
    [
        ({"email": "ana@"}, False),
        ({"password2": "Otra-Clave-Distinta-321"}, True),
    ],
    ids=["correo_invalido", "passwords_distintas"],
)
def test_errores_conservan_datos_validos(client, datos_registro, cambios, conserva_email):
    respuesta = client.post(reverse("usuarios:registro"), {**datos_registro, **cambios})

    html = respuesta.content.decode()
    assert 'value="Ana"' in input_de(html, "first_name")
    assert 'value="Pérez"' in input_de(html, "last_name")
    if conserva_email:
        assert 'value="ana@lab.com"' in input_de(html, "email")


# Paso 2: revisión y confirmación


def test_confirmar_crea_cuenta_pendiente(client, datos_registro, password_registro):
    respuesta = client.post(reverse("usuarios:registro"), datos_registro)
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("usuarios:registro_confirmar")

    revision = client.get(reverse("usuarios:registro_confirmar"))
    html = revision.content.decode()
    assert revision.status_code == 200
    for texto in ("Ana", "Pérez", "ana@lab.com", AVISO_REVISION):
        assert texto in html

    confirmacion = client.post(reverse("usuarios:registro_confirmar"), {"accion": "confirmar"})
    assert confirmacion.status_code == 302
    assert confirmacion.url == reverse("usuarios:registro_recibido")

    usuario = get_user_model().objects.get()
    assert usuario.email == "ana@lab.com"
    assert not usuario.is_active
    assert not usuario.is_staff
    assert not usuario.is_superuser
    assert usuario.check_password(password_registro)
    assert CLAVE_SESION not in client.session

    recibido = client.get(confirmacion.url)
    assert MENSAJE_EXITO in recibido.content.decode()


def test_volver_precarga_datos_sin_password(en_revision):
    respuesta = en_revision.get(reverse("usuarios:registro"))

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert 'value="Ana"' in input_de(html, "first_name")
    assert 'value="Pérez"' in input_de(html, "last_name")
    assert 'value="ana@lab.com"' in input_de(html, "email")
    assert "value=" not in input_de(html, "password1")
    assert "value=" not in input_de(html, "password2")
    assert cantidad_usuarios() == 0


def test_cancelar_no_crea_cuenta(en_revision):
    respuesta = en_revision.post(reverse("usuarios:registro_confirmar"), {"accion": "cancelar"})

    assert respuesta.status_code == 302
    assert respuesta.url == reverse("usuarios:registro")
    assert "Registro cancelado." in en_revision.get(respuesta.url).content.decode()
    assert CLAVE_SESION not in en_revision.session
    assert cantidad_usuarios() == 0

    confirmar = en_revision.get(reverse("usuarios:registro_confirmar"))
    assert confirmar.status_code == 302
    assert confirmar.url == reverse("usuarios:registro")


def test_confirmacion_repetida_crea_una_cuenta(en_revision):
    url = reverse("usuarios:registro_confirmar")
    en_revision.post(url, {"accion": "confirmar"})

    segunda = en_revision.post(url, {"accion": "confirmar"})
    assert segunda.status_code == 302
    assert segunda.url == reverse("usuarios:registro_recibido")
    assert MENSAJE_EXITO in en_revision.get(segunda.url).content.decode()
    assert cantidad_usuarios() == 1


def test_integrity_error_no_crea_segunda_cuenta(en_revision):
    get_user_model().objects.create_user(
        email="ana@lab.com",
        password=PASSWORD_EXISTENTE,
        first_name="Ana",
        last_name="Otra",
        is_active=False,
    )

    respuesta = en_revision.post(reverse("usuarios:registro_confirmar"), {"accion": "confirmar"})

    assert respuesta.status_code == 302
    assert respuesta.url == reverse("usuarios:registro")
    assert MENSAJE_NO_DISPONIBLE in en_revision.get(respuesta.url).content.decode()
    assert cantidad_usuarios() == 1


def test_error_de_base_informa_sin_crear(en_revision, monkeypatch):
    def falla(datos):
        raise DatabaseError("base caída")

    monkeypatch.setattr("usuarios.views.crear_usuario_pendiente", falla)

    respuesta = en_revision.post(reverse("usuarios:registro_confirmar"), {"accion": "confirmar"})

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert AVISO_REVISION in html
    assert "No se pudo completar el registro. Intentá nuevamente." in html
    assert cantidad_usuarios() == 0
    assert CLAVE_SESION in en_revision.session


def test_password_no_aparece_en_respuestas(client, datos_registro, password_registro):
    con_error = client.post(
        reverse("usuarios:registro"),
        {**datos_registro, "password2": "Otra-Clave-Distinta-321"},
    )
    assert con_error.status_code == 200
    assert password_registro not in con_error.content.decode()
    assert "Otra-Clave-Distinta-321" not in con_error.content.decode()

    client.post(reverse("usuarios:registro"), datos_registro)
    revision = client.get(reverse("usuarios:registro_confirmar"))
    assert password_registro not in revision.content.decode()

    recibido = client.post(
        reverse("usuarios:registro_confirmar"), {"accion": "confirmar"}, follow=True
    )
    assert MENSAJE_EXITO in recibido.content.decode()
    assert password_registro not in recibido.content.decode()


def test_sesion_guarda_hash(client, datos_registro, password_registro):
    client.post(reverse("usuarios:registro"), datos_registro)

    datos = client.session[CLAVE_SESION]
    assert set(datos) == {"first_name", "last_name", "email", "password"}
    assert datos["password"] != password_registro
    assert check_password(password_registro, datos["password"])
