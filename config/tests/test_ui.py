import pytest
from django.template.loader import render_to_string

from config.ui import iniciales, tipo_estado


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("Aguas del Sur S.A.", "AS"),
        ("Juan Pérez", "JP"),
        ("Cooperativa de Aguas Rurales", "CA"),
        ("ñandú sur", "ÑS"),
        ("Juan pablo dominguez lucia", "JP"),
        ("juan jose", "JJ"),
        ("Elena", "E"),
        ("", ""),
        (None, ""),
        ("123 Aguas", "A"),
    ],
)
def test_iniciales(texto, esperado):
    assert iniciales(texto) == esperado


def test_icono_inserta_el_svg_con_la_clase_pedida():
    html = render_to_string("ui/icono.html", {"nombre": "search", "clase": "size-4"})
    assert '<svg class="size-4" aria-hidden="true"' in html


def test_estado_marca_el_tipo():
    html = render_to_string("ui/estado.html", {"estado": "Activo", "tipo": "success"})
    assert 'data-estado="success"' in html
    assert "Activo" in html


@pytest.mark.parametrize(
    ("estado", "esperado"),
    [
        ("ingresada", "info"),
        ("pendiente_analisis", "warning"),
        ("en_proceso", "info"),
        ("finalizado", "success"),
        ("informe_generado", "success"),
        ("pendiente", "neutral"),
        ("cargada", "info"),
        ("completada", "success"),
        ("desconocido", "neutral"),
    ],
)
def test_tipo_estado(estado, esperado):
    assert tipo_estado(estado) == esperado
