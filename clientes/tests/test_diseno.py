"""Estructura de la interfaz de clientes (SCRUM-67, US2 y US3)."""

import re

import pytest
from django.template.loader import render_to_string
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


# Consulta de clientes (US3)


def test_busqueda_con_resultados_muestra_cantidad_y_ver_ficha(
    cliente_autenticado, clientes_busqueda
):
    html = cliente_autenticado.get(reverse("clientes:buscar"), {"q": "María"}).content.decode()

    assert "2 clientes encontrados" in html
    for cliente in Cliente.objects.filter(nombre="María Gómez"):
        url = reverse("clientes:detalle", args=[cliente.pk])
        assert re.search(rf'href="{url}"[^>]*>.*?Ver ficha', html, re.S)


def test_busqueda_sin_resultados_muestra_el_estado_vacio(cliente_autenticado, clientes_busqueda):
    html = cliente_autenticado.get(reverse("clientes:buscar"), {"q": "zzzz"}).content.decode()

    vacio = re.search(r'data-componente="estado-vacio".*?</div>\s*</div>', html, re.S)
    assert vacio
    assert "No se encontraron clientes para «zzzz»." in vacio.group(0)


def test_ficha_tiene_encabezado_con_nombre_y_estado(cliente_autenticado, cliente_existente):
    html = cliente_autenticado.get(
        reverse("clientes:detalle", args=[cliente_existente.pk])
    ).content.decode()

    encabezado = re.search(r"<h1[^>]*>(.*?)</h1>(.*?)</header>", html, re.S)
    assert "Aguas del Sur S.A." in encabezado.group(1)
    assert 'data-estado="success">Activo' in encabezado.group(2)


def test_ficha_de_cliente_inactivo_muestra_la_etiqueta_neutral(cliente_existente):
    # La vista no abre la ficha de un cliente inactivo (redirige a la búsqueda), pero el
    # template debe mostrar el estado correcto si se usa con uno (FR-009).
    cliente_existente.activo = False

    html = render_to_string("clientes/detalle.html", {"cliente": cliente_existente})

    assert 'data-estado="neutral">Inactivo' in html


def test_ficha_muestra_raya_en_los_datos_vacios_y_sus_acciones(
    cliente_autenticado, cliente_existente
):
    html = cliente_autenticado.get(
        reverse("clientes:detalle", args=[cliente_existente.pk])
    ).content.decode()

    assert re.search(r"<dt>Nombre</dt>\s*<dd>—</dd>", html)
    assert re.search(r"<dt>Teléfono</dt>\s*<dd>—</dd>", html)
    assert "Editar cliente" in html
    assert "Volver a la búsqueda" in html
