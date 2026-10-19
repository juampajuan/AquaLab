import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_inicio_sin_sesion_redirige_al_login(client):
    respuesta = client.get(reverse("inicio"))

    assert respuesta.status_code == 302
    assert respuesta.url.startswith(reverse("admin:login"))
