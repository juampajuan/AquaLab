"""Ayuda en formularios (US 9.1): crear estudio, agregar prueba, tipos de estudio y mediciones."""

import re

import pytest
from django.test import Client
from django.urls import reverse

from estudios.tests.utiles import cargar

pytestmark = pytest.mark.django_db


def tooltip(html, id_):
    encontrado = re.search(rf'<span role="tooltip" id="{id_}"[^>]*>(.*?)</span>', html)
    return encontrado[1].strip() if encontrado else None


def test_crear_estudio_explica_el_tipo(cliente_http, tipo):
    html = cliente_http.get(reverse("estudios:crear")).content.decode()
    assert tooltip(html, "id_tipo_helptext")
    assert 'id="id_muestra_helptext"' not in html


def test_agregar_prueba_explica_que_pruebas_se_listan(cliente_http, estudio, prueba_extra):
    html = cliente_http.get(reverse("estudios:agregar_prueba", args=[estudio.pk])).content.decode()
    assert tooltip(html, "id_prueba_helptext")


def test_tipos_de_estudio_ayuda_en_tooltip_e_instruccion_visible(gestor, pruebas):
    cliente = Client()
    cliente.force_login(gestor)
    html = cliente.get(reverse("estudios:tipos_crear")).content.decode()

    assert tooltip(html, "id_pruebas_helptext")
    instruccion = re.search(r'<p class="campo-ayuda" id="id_pruebas_instruccion">(.*?)</p>', html)
    assert "Ctrl" in instruccion[1]
    assert re.search(
        r'<select[^>]*name="pruebas"[^>]*'
        r'aria-describedby="id_pruebas_helptext id_pruebas_instruccion"',
        html,
    )
    assert html.count("Ctrl") == 1


# --- Mediciones (US 2, escenario 6) ---

FORMATO = ("coma o punto", "Ausente/Presente")


def controles_de_medicion(html):
    return re.findall(r'<(?:input|select)[^>]*name="medicion_\d+"[^>]*>', html)


def comprobar_tabla(html):
    aviso = re.search(r'<div class="aviso aviso-info[^"]*"[^>]*>(.*?)</div>\s*</div>', html, re.S)
    for texto in FORMATO:
        assert texto in aviso[1]
    encabezado = next(th for th in re.findall(r"<th>(.*?)</th>", html, re.S) if "Medición" in th)
    assert 'data-lado="derecha"' in encabezado
    assert 'data-posicion="abajo"' in encabezado, "arriba lo recorta el contenedor de la tabla"
    assert tooltip(encabezado, "ayuda-medicion")
    controles = controles_de_medicion(html)
    assert controles
    for control in controles:
        assert re.search(r'aria-describedby="ayuda-medicion[ "]', control)


def test_cargar_mediciones_muestra_formato_y_significado(cliente_http, estudio_mediciones):
    url = reverse("estudios:cargar_mediciones", args=[estudio_mediciones.pk])
    comprobar_tabla(cliente_http.get(url).content.decode())


def test_con_error_la_medicion_queda_descrita_por_la_ayuda_y_el_error(
    cliente_http, estudio_mediciones, asignaciones_medicion
):
    nombre = f"medicion_{asignaciones_medicion['TEST-VOL'].pk}"
    respuesta = cliente_http.post(
        reverse("estudios:cargar_mediciones", args=[estudio_mediciones.pk]),
        {"accion": "revisar", nombre: "abc"},
    )
    assert f'aria-describedby="ayuda-medicion id_{nombre}_error"' in respuesta.content.decode()


def test_corregir_mediciones_muestra_formato_y_significado(cliente_http, estudio_de, empleado):
    estudio = estudio_de("CL-", "PH")
    cargar(estudio, empleado, CL_="2.35", PH="7.20")
    url = reverse("estudios:corregir_mediciones", args=[estudio.pk])
    comprobar_tabla(cliente_http.get(url).content.decode())
