import pytest
from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import Client
from django.urls import reverse

from .conftest import PASSWORD_EXISTENTE

pytestmark = pytest.mark.django_db


def huella_de(client):
    return client.get(reverse("inicio")).context["huella_sesion"]


def test_revalidacion_solo_misma_sesion(client, usuario_aprobado):
    assert client.login(email=usuario_aprobado.email, password=PASSWORD_EXISTENTE)
    huella = huella_de(client)
    clave = client.session.session_key
    antes = Session.objects.get(session_key=clave)
    respuesta = client.get(reverse("usuarios:sesion"), HTTP_X_AQUALAB_SESION=huella)
    despues = Session.objects.get(session_key=clave)
    assert respuesta.status_code == 204
    assert respuesta.content == b""
    assert antes.expire_date == despues.expire_date
    assert antes.session_data == despues.session_data
    for valor in ["", "otra-huella"]:
        assert (
            client.get(reverse("usuarios:sesion"), HTTP_X_AQUALAB_SESION=valor).status_code == 409
        )
    assert client.post(reverse("usuarios:sesion")).status_code == 405
    anonimo = Client()
    assert anonimo.get(reverse("usuarios:sesion"), HTTP_X_AQUALAB_SESION=huella).status_code == 302


def test_huella_cambia_con_nueva_sesion(client, usuario_aprobado):
    assert client.login(email=usuario_aprobado.email, password=PASSWORD_EXISTENTE)
    vieja = huella_de(client)
    client.post(reverse("usuarios:logout"))
    assert client.login(email=usuario_aprobado.email, password=PASSWORD_EXISTENTE)
    assert huella_de(client) != vieja
    assert client.get(reverse("usuarios:sesion"), HTTP_X_AQUALAB_SESION=vieja).status_code == 409
    assert (
        client.cookies[settings.SESSION_COOKIE_NAME].value
        not in client.get(reverse("inicio")).content.decode()
    )


def test_rotacion_y_otro_usuario_invalidan_huella(client, usuario_aprobado, administrador):
    assert client.login(email=usuario_aprobado.email, password=PASSWORD_EXISTENTE)
    vieja = huella_de(client)
    sesion = client.session
    sesion.cycle_key()
    client.cookies[settings.SESSION_COOKIE_NAME] = sesion.session_key
    assert huella_de(client) != vieja
    assert client.get(reverse("usuarios:sesion"), HTTP_X_AQUALAB_SESION=vieja).status_code == 409
    client.logout()
    assert client.login(email=administrador.email, password=PASSWORD_EXISTENTE)
    assert huella_de(client) != vieja
    assert client.get(reverse("usuarios:sesion"), HTTP_X_AQUALAB_SESION=vieja).status_code == 409
