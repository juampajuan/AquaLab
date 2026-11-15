"""Lo que dicen las herramientas coincide con las pantallas (FR-005, SC-001)."""

import html as html_lib
import re

import pytest
from django.urls import reverse

from .conftest import ejecutar

pytestmark = pytest.mark.django_db


def fila(html, codigo):
    """La fila de la prueba en la tabla del detalle del estudio."""
    for tr in re.findall(r"<tr[^>]*>.*?</tr>", html, re.S):
        if f">{codigo}<" in tr or f"{codigo}</" in tr:
            return re.sub(r"\s+", " ", html_lib.unescape(tr))
    raise AssertionError(f"No está la fila de {codigo}")


def test_detalle_estudio_igual_a_la_pantalla(cliente_http, empleado, estudio_completo):
    salida = ejecutar(empleado, "detalle_estudio", numero=estudio_completo.pk).salida
    html = cliente_http.get(
        reverse("estudios:detalle", args=[estudio_completo.pk])
    ).content.decode()
    texto = re.sub(r"\s+", " ", html_lib.unescape(html))
    assert salida["datos"]["estado"] in texto
    for prueba in salida["datos"]["pruebas"]:
        celda = fila(html, prueba["codigo"])
        assert prueba["estado"] in celda, prueba["codigo"]
        if prueba["evaluacion"]:
            assert prueba["evaluacion"] in celda, prueba["codigo"]
        if prueba["limite"]:
            assert prueba["limite"] in celda, prueba["codigo"]
        # «< LD» sale como en el informe; el detalle muestra el valor medido.
        if prueba["resultado"] and not prueba["resultado"].startswith("<"):
            assert prueba["resultado"] in celda, prueba["codigo"]
        if prueba["unidad"]:
            assert prueba["unidad"] in celda, prueba["codigo"]
        if prueba["sin_resultado"]:
            assert prueba["sin_resultado"] in celda, prueba["codigo"]


def test_buscar_muestra_igual_a_la_ficha(cliente_http, empleado, estudio_completo, muestra):
    datos = ejecutar(empleado, "buscar_muestra", numero_pi=200001).salida["datos"]
    html = cliente_http.get(reverse("muestras:detalle", args=[muestra.pk])).content.decode()
    texto = re.sub(r"\s+", " ", html_lib.unescape(html))
    for campo in ("cliente", "origen", "sitio_extraccion", "fecha_ingreso", "tipo_vertido"):
        assert datos[campo] in texto, campo
    for estudio in datos["estudios"]:
        assert estudio["tipo"] in texto
        assert estudio["estado"] in texto
        assert f"{estudio['pruebas_completadas']} / {estudio['total_pruebas']}" in texto
