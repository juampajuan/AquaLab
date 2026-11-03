"""Ayuda en formularios (US 9.1): registro de muestra."""

import re

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

CON_AYUDA = (
    "origen",
    "origen_nuevo",
    "fecha_muestreo",
    "fecha_ingreso",
    "sitio_extraccion",
    "tipo_vertido",
    "nombre",
    "responsable_muestreo",
)


def tooltip(html, nombre):
    encontrado = re.search(
        rf'<span role="tooltip" id="id_{nombre}_helptext"[^>]*>(.*?)</span>', html
    )
    return encontrado[1].strip() if encontrado else None


@pytest.fixture
def html(cliente_autenticado, cliente_a):
    return cliente_autenticado.get(reverse("muestras:registrar")).content.decode()


@pytest.mark.parametrize("nombre", CON_AYUDA)
def test_campos_que_no_se_explican_solos_tienen_ayuda(html, nombre):
    assert tooltip(html, nombre)


def test_el_cliente_no_tiene_ayuda(html):
    assert 'id="id_cliente_helptext"' not in html


def test_la_ayuda_del_nombre_pasa_al_tooltip(html):
    assert "Muestra 6" in tooltip(html, "nombre")
    assert 'class="campo-ayuda"' not in html
