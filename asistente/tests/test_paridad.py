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


def test_fuera_de_norma_igual_a_la_pantalla(cliente_http, empleado, estudio_completo):
    """Las que devuelve `solo_fuera_de_norma` son las marcadas «Fuera de norma» en el detalle."""
    salida = ejecutar(
        empleado, "detalle_estudio", numero=estudio_completo.pk, solo_fuera_de_norma=True
    ).salida
    html = cliente_http.get(
        reverse("estudios:detalle", args=[estudio_completo.pk])
    ).content.decode()
    codigos = ["PH", "CL-", "COND", "ECOLI", "TURBIDEZ", "TEMPERATURA"]
    en_pantalla = [c for c in codigos if "Fuera de norma" in fila(html, c)]
    assert [p["codigo"] for p in salida["datos"]["pruebas"]] == en_pantalla == ["CL-"]


def test_estudios_de_cliente_igual_al_historial(cliente_http, empleado, lacteos):
    """El orden y los estados son los de `clientes:historial`."""
    cliente = lacteos["cliente"]
    datos = ejecutar(empleado, "estudios_de_cliente", cliente_id=cliente.pk).salida["datos"]
    contexto = cliente_http.get(reverse("clientes:historial", args=[cliente.pk])).context
    del_historial = [
        (e.pk, e.get_estado_display())
        for muestra in contexto["page_obj"].object_list
        for e in muestra.estudios_historial
    ]
    assert [(e["numero"], e["estado"]) for e in datos["estudios"]] == del_historial[:10]
