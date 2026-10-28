"""Estructura de la interfaz de muestras (SCRUM-67, US2)."""

import pytest
from django.urls import reverse

from config.tests.ayudas_diseno import es_obligatorio, radios_de, tiene_componentes_de_confirmacion

pytestmark = pytest.mark.django_db


def test_tipo_de_vertido_son_radios_con_agua_por_defecto(cliente_autenticado):
    html = cliente_autenticado.get(reverse("muestras:registrar")).content.decode()

    assert radios_de(html, "tipo_vertido") == {"agua": True, "cloacal": False, "canal": False}


def test_registro_marca_solo_los_campos_obligatorios(cliente_autenticado):
    html = cliente_autenticado.get(reverse("muestras:registrar")).content.decode()

    for campo in ("cliente", "fecha_muestreo", "fecha_ingreso", "sitio_extraccion"):
        assert es_obligatorio(html, campo), campo
    for campo in ("nombre", "responsable_muestreo", "origen_nuevo"):
        assert not es_obligatorio(html, campo), campo


def test_confirmacion_usa_los_componentes_comunes(cliente_autenticado, datos_muestra_validos):
    respuesta = cliente_autenticado.post(reverse("muestras:registrar"), datos_muestra_validos)
    html = cliente_autenticado.get(respuesta.url).content.decode()

    assert tiene_componentes_de_confirmacion(html)
    assert 'data-estado="info">Ingresada' in html
