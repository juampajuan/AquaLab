"""Componentes compartidos de la interfaz (SCRUM-67, US2 escenario 5)."""

import re

import pytest
from django.contrib.messages import constants
from django.contrib.messages.storage.base import Message
from django.template.loader import render_to_string


@pytest.mark.parametrize(
    ("nivel", "esperado"),
    [
        (constants.SUCCESS, "exito"),
        (constants.ERROR, "error"),
        (constants.WARNING, "advertencia"),
        (constants.INFO, "info"),
    ],
)
def test_cada_mensaje_se_dibuja_segun_su_nivel_y_se_puede_cerrar(nivel, esperado):
    html = render_to_string("ui/mensajes.html", {"messages": [Message(nivel, "Texto de prueba")]})

    aviso = re.search(r'<div[^>]*data-nivel="([^"]+)"[^>]*>(.*?)</button>', html, re.S)
    assert aviso.group(1) == esperado
    assert "Texto de prueba" in aviso.group(2)
    assert "data-cerrar-mensaje" in aviso.group(2)


def test_sin_mensajes_no_dibuja_nada():
    assert render_to_string("ui/mensajes.html", {"messages": []}).strip() == ""


@pytest.mark.parametrize("url", ["", "/estudios/buscar/?pendiente=mediciones"])
def test_indicador_url_opcional(url):
    html = render_to_string(
        "ui/indicador.html",
        {
            "url": url,
            "nombre": "mediciones-pendientes",
            "titulo": "Mediciones",
            "valor": 3,
            "icono": "microscope",
        },
    )
    assert 'data-indicador="mediciones-pendientes"' in html
    assert "data-valor>3<" in html
    assert ("<a " in html) == bool(url)
    assert html.count("<a ") <= 1
    if url:
        assert "href=" in html
        assert "focus-visible:" in html


def test_ayuda_filtro_pendiente_alineada():
    """La ayuda cambia de alineación y la tabla contiene su texto accesible."""
    from django.core.paginator import Paginator

    from estudios.forms import FiltrarEstudiosForm

    html = render_to_string(
        "estudios/buscar.html",
        {
            "form": FiltrarEstudiosForm(),
            "page_obj": Paginator([{"pk": 1, "muestra": {"pk": 1}}], 20).get_page(1),
        },
    )
    assert "[&_.ayuda-texto]:left-0" in html
    assert "xl:[&_.ayuda-texto]:right-0" in html
    assert html.count("sm:max-xl:[&_.ayuda-texto]:right-0") == 2
    assert 'aria-label="Ayuda: Trabajo pendiente"' in html
    assert '<th class="relative"><span class="sr-only">Acciones</span></th>' in html
    assert re.search(r'data-lado="derecha"[^>]*><button[^>]*aria-label="Ayuda: Identificador', html)
