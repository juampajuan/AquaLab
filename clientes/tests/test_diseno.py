"""Estructura de la interfaz de clientes (SCRUM-67, US2)."""

import pytest
from django.urls import reverse

from clientes.models import Cliente
from config.tests.ayudas_diseno import es_obligatorio, radios_de, tiene_componentes_de_confirmacion

pytestmark = pytest.mark.django_db


def test_alta_dibuja_tipo_de_documento_como_radios_sin_opcion_vacia(cliente_autenticado):
    html = cliente_autenticado.get(reverse("clientes:registrar")).content.decode()

    assert radios_de(html, "tipo_documento") == {"DNI": False, "CUIT": False}


def test_edicion_marca_el_tipo_de_documento_del_cliente(cliente_autenticado, otro_cliente):
    html = cliente_autenticado.get(
        reverse("clientes:editar", args=[otro_cliente.pk])
    ).content.decode()

    assert radios_de(html, "tipo_documento") == {"DNI": True, "CUIT": False}


def test_alta_con_cuit_elegido_por_radio_sigue_funcionando(
    cliente_autenticado, datos_cliente_empresa
):
    cliente_autenticado.post(reverse("clientes:registrar"), datos_cliente_empresa)
    cliente_autenticado.post(reverse("clientes:registrar_confirmar"), {"accion": "confirmar"})

    assert Cliente.objects.get().tipo_documento == "CUIT"


def test_alta_marca_solo_los_campos_obligatorios(cliente_autenticado):
    html = cliente_autenticado.get(reverse("clientes:registrar")).content.decode()

    for campo in ("tipo_documento", "numero_documento", "email"):
        assert es_obligatorio(html, campo), campo
    for campo in ("nombre", "razon_social", "telefono", "domicilio"):
        assert not es_obligatorio(html, campo), campo


def test_confirmacion_de_alta_usa_los_componentes_comunes(en_revision):
    html = en_revision.get(reverse("clientes:registrar_confirmar")).content.decode()

    assert tiene_componentes_de_confirmacion(html)


def test_confirmacion_de_edicion_usa_los_componentes_comunes(
    cliente_autenticado, cliente_existente, datos_edicion_validos
):
    url_editar = reverse("clientes:editar", args=[cliente_existente.pk])
    respuesta = cliente_autenticado.post(url_editar, datos_edicion_validos)
    html = cliente_autenticado.get(respuesta.url).content.decode()

    assert tiene_componentes_de_confirmacion(html)
