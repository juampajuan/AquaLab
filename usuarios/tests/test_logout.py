import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse

from .conftest import PASSWORD_EXISTENTE

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("ruta", ["usuarios:logout", "admin:logout"])
@pytest.mark.parametrize("next_url", ["/admin/", "https://externo.example/"])
def test_logout_csrf_destino_y_repeticion(cliente_csrf, administrador, ruta, next_url):
    assert cliente_csrf.login(email=administrador.email, password=PASSWORD_EXISTENTE)
    cliente_csrf.get(reverse("inicio"))
    token = cliente_csrf.cookies["csrftoken"].value
    url = reverse(ruta) + "?next=" + next_url
    assert cliente_csrf.get(url).status_code == 405
    for datos in [{}, {"csrfmiddlewaretoken": "invalido"}]:
        assert cliente_csrf.post(url, datos).status_code == 403
        assert "_auth_user_id" in cliente_csrf.session
    respuesta = cliente_csrf.post(url, {"csrfmiddlewaretoken": token, "next": next_url})
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("usuarios:login")
    assert "_auth_user_id" not in cliente_csrf.session
    assert cliente_csrf.post(url, {"csrfmiddlewaretoken": token}).status_code == 302


def test_invalida_cookie_compartida_no_otra_sesion(client, usuario_aprobado):
    assert client.login(email=usuario_aprobado.email, password=PASSWORD_EXISTENTE)
    vieja = client.cookies[settings.SESSION_COOKIE_NAME].value
    otra_pestana = Client()
    otra_pestana.cookies[settings.SESSION_COOKIE_NAME] = vieja
    independiente = Client()
    assert independiente.login(email=usuario_aprobado.email, password=PASSWORD_EXISTENTE)
    sesion = client.session
    sesion["cliente_pendiente"] = {"nombre": "Borrador"}
    sesion.save()
    client.post(reverse("usuarios:logout"))
    assert otra_pestana.get(reverse("inicio")).status_code == 302
    assert independiente.get(reverse("inicio")).status_code == 200
    assert "cliente_pendiente" not in otra_pestana.session
