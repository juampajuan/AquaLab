import pytest
from django.urls import reverse

from .conftest import PASSWORD_EXISTENTE

pytestmark = pytest.mark.django_db


def test_login_publico(client):
    respuesta = client.get(reverse("usuarios:login"))
    assert respuesta.status_code == 200
    assert "Crear cuenta" in respuesta.content.decode()


@pytest.mark.parametrize("destino", ["/clientes/registrar/", "https://externo.example/"])
def test_login_aprobado_destino_fijo(client, usuario_aprobado, destino):
    respuesta = client.post(
        reverse("usuarios:login") + "?next=" + destino,
        {
            "username": usuario_aprobado.email,
            "password": PASSWORD_EXISTENTE,
            "next": destino,
        },
    )
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("inicio")
    assert client.session["_auth_user_id"] == str(usuario_aprobado.pk)
    assert usuario_aprobado.get_full_name() in client.get(respuesta.url).content.decode()


@pytest.mark.parametrize("metodo", ["get", "post"])
def test_autenticado_vuelve_inicio(client, usuario_aprobado, metodo):
    assert client.login(email=usuario_aprobado.email, password=PASSWORD_EXISTENTE)
    respuesta = getattr(client, metodo)(reverse("usuarios:login"), {"next": "/admin/"})
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("inicio")


def test_login_exige_csrf(cliente_csrf, usuario_aprobado):
    url = reverse("usuarios:login")
    datos = {"username": usuario_aprobado.email, "password": PASSWORD_EXISTENTE}
    assert cliente_csrf.post(url, datos).status_code == 403
    assert "_auth_user_id" not in cliente_csrf.session
    cliente_csrf.get(url)
    datos["csrfmiddlewaretoken"] = cliente_csrf.cookies["csrftoken"].value
    assert cliente_csrf.post(url, datos).status_code == 302
    assert "_auth_user_id" in cliente_csrf.session
