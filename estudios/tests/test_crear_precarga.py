"""Crear estudio precargado por GET (US 10.3, contracts/enlaces-precargados.md)."""

import re

import pytest
from django.http import QueryDict
from django.urls import reverse

from estudios.forms import valores_iniciales_estudio
from estudios.models import Estudio, TipoEstudio

pytestmark = pytest.mark.django_db

URL_CREAR = reverse("estudios:crear")


def elegida(html, nombre):
    select = re.search(rf'<select[^>]*name="{nombre}"[^>]*>(.*?)</select>', html, re.S).group(1)
    opcion = re.search(r'<option value="([^"]*)"[^>]*selected', select)
    return opcion.group(1) or None if opcion else None


def test_get_precarga_muestra_y_tipo(cliente_http, muestra, tipo):
    html = cliente_http.get(f"{URL_CREAR}?muestra={muestra.pk}&tipo={tipo.pk}").content.decode()
    assert elegida(html, "muestra") == str(muestra.pk)
    assert elegida(html, "tipo") == str(tipo.pk)
    assert not Estudio.objects.exists()


def test_volver_gana_sobre_los_parametros(cliente_http, muestra, tipo):
    otro = TipoEstudio.objects.create(nombre="Otro tipo")
    respuesta = cliente_http.post(URL_CREAR, {"muestra": muestra.pk, "tipo": tipo.pk})
    clave = respuesta.url.split("solicitud=")[1]
    html = cliente_http.get(f"{URL_CREAR}?volver={clave}&tipo={otro.pk}").content.decode()
    assert elegida(html, "tipo") == str(tipo.pk)


@pytest.mark.parametrize("valor", ["999999", "abc", ""])
def test_tipo_invalido_se_descarta(cliente_http, muestra, valor):
    respuesta = cliente_http.get(f"{URL_CREAR}?muestra={muestra.pk}&tipo={valor}")
    assert respuesta.status_code == 200
    assert elegida(respuesta.content.decode(), "tipo") is None


def test_tipo_inactivo_se_descarta(cliente_http, muestra, tipo_inactivo):
    iniciales = valores_iniciales_estudio(
        QueryDict(f"muestra={muestra.pk}&tipo={tipo_inactivo.pk}")
    )
    assert iniciales == {"muestra": str(muestra.pk)}
    html = cliente_http.get(
        f"{URL_CREAR}?muestra={muestra.pk}&tipo={tipo_inactivo.pk}"
    ).content.decode()
    assert elegida(html, "tipo") is None


def test_sin_parametros(cliente_http):
    assert valores_iniciales_estudio(QueryDict("")) is None
    assert cliente_http.get(URL_CREAR).status_code == 200
