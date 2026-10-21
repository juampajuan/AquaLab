import pytest
from django.urls import reverse

from .conftest import PASSWORD_EXISTENTE

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "ruta",
    [
        "inicio",
        "clientes:registrar",
        "clientes:registrar_confirmar",
        "admin:index",
        "usuarios:sesion",
    ],
)
def test_cache_protegida(client, administrador, ruta):
    assert client.login(email=administrador.email, password=PASSWORD_EXISTENTE)
    respuesta = client.get(reverse(ruta))
    for directiva in ["private", "no-store", "no-cache", "must-revalidate"]:
        assert directiva in respuesta.headers["Cache-Control"]


@pytest.mark.parametrize(
    "ruta", ["usuarios:login", "usuarios:registro", "usuarios:registro_recibido"]
)
def test_anonimo_sin_guardia_ni_sesion(client, ruta):
    respuesta = client.get(reverse(ruta))
    assert respuesta.status_code == 200
    assert "sesion.js" not in respuesta.content.decode()
    assert "sessionid" not in respuesta.cookies


def test_layouts_guardia_y_logout(client, administrador):
    assert client.login(email=administrador.email, password=PASSWORD_EXISTENTE)
    for ruta in ["inicio", "clientes:registrar", "admin:index"]:
        respuesta = client.get(reverse(ruta))
        html = respuesta.content.decode()
        assert "sesion.js" in html
        assert "data-huella=" in html
        assert reverse("usuarios:logout") in html
        assert "csrfmiddlewaretoken" in html


def test_error_formulario_y_login_no_cache(client, usuario_aprobado):
    respuesta = client.post(
        reverse("usuarios:login"),
        {
            "username": usuario_aprobado.email,
            "password": "incorrecta",
        },
    )
    assert respuesta.status_code == 200
    assert "no-store" in respuesta.headers["Cache-Control"]
    assert client.login(email=usuario_aprobado.email, password=PASSWORD_EXISTENTE)
    respuesta = client.post(reverse("clientes:registrar"), {})
    assert respuesta.status_code == 200
    assert "no-store" in respuesta.headers["Cache-Control"]
    assert "sesion.js" in respuesta.content.decode()
