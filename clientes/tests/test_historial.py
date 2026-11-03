"""Pantalla del historial del cliente (US 3.3)."""

import re
from datetime import date

import pytest
from django.conf import settings
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from clientes.models import Cliente
from estudios.models import EstadoEstudio, Estudio, TipoEstudio
from informes.models import Informe
from muestras.models import Muestra

pytestmark = pytest.mark.django_db


def url(cliente, **parametros):
    base = reverse("clientes:historial", args=[cliente.pk])
    if parametros:
        from urllib.parse import urlencode

        base += "?" + urlencode(parametros)
    return base


def html_de(cliente_http, cliente, **parametros):
    respuesta = cliente_http.get(url(cliente, **parametros))
    assert respuesta.status_code == 200
    return respuesta.content.decode()


def muestras_en(html):
    return [int(n) for n in re.findall(r'data-muestra="(\d+)"', html)]


def estudios_en(html):
    return [int(n) for n in re.findall(r'data-estudio="(\d+)"', html)]


@pytest.fixture
def otro(db):
    return Cliente.objects.create(
        nombre="Otra Persona", tipo_documento="DNI", numero_documento="27999888", email="o@x.com"
    )


# --- US1: ver el historial -------------------------------------------------------------------


def test_ficha_ofrece_historial(cliente_autenticado, cliente_existente):
    html = cliente_autenticado.get(
        reverse("clientes:detalle", args=[cliente_existente.pk])
    ).content.decode()

    assert re.search(rf'href="{re.escape(url(cliente_existente))}"[^>]*>.*?Historial', html, re.S)


def test_lista_muestras_del_cliente(
    cliente_autenticado, cliente_existente, otro, muestra_de, estudio_en
):
    muestra = muestra_de(cliente_existente, date(2026, 10, 10), 200001, origen="Tanque norte")
    estudio = estudio_en(muestra, EstadoEstudio.EN_PROCESO)
    muestra_de(otro, date(2026, 10, 11), 200002)

    html = html_de(cliente_autenticado, cliente_existente)

    assert muestras_en(html) == [200001]
    assert "10/10/2026" in html
    assert "Tanque norte" in html
    assert estudios_en(html) == [estudio.pk]
    assert f"Estudio N° {estudio.pk}" in html
    assert "Agua de red" in html
    assert "En proceso" in html
    assert "200002" not in html


def test_muestra_tipo_guardado(cliente_autenticado, cliente_existente, muestra_de, estudio_en):
    estudio = estudio_en(muestra_de(cliente_existente, date(2026, 10, 1), 200001))
    TipoEstudio.objects.filter(pk=estudio.tipo_id).update(nombre="Nombre nuevo del catálogo")

    html = html_de(cliente_autenticado, cliente_existente)

    assert "Agua de red" in html
    assert "Nombre nuevo del catálogo" not in html


def test_orden_en_pantalla(cliente_autenticado, cliente_existente, muestra_de):
    muestra_de(cliente_existente, date(2026, 9, 15), 200001)
    muestra_de(cliente_existente, date(2026, 10, 25), 200002)
    muestra_de(cliente_existente, date(2026, 10, 10), 200003)

    html = html_de(cliente_autenticado, cliente_existente)

    assert muestras_en(html) == [200002, 200003, 200001]


def test_muestra_sin_estudios(cliente_autenticado, cliente_existente, muestra_de):
    muestra_de(cliente_existente, date(2026, 10, 1), 200001)

    assert "Sin estudios" in html_de(cliente_autenticado, cliente_existente)


def test_cliente_sin_muestras(cliente_autenticado, cliente_existente):
    html = html_de(cliente_autenticado, cliente_existente)

    assert "Este cliente no tiene muestras registradas." in html
    assert "Ninguna muestra coincide con los filtros." not in html


def test_encabezado_identifica_cliente(cliente_autenticado, cliente_existente):
    html = html_de(cliente_autenticado, cliente_existente)

    assert "Aguas del Sur S.A." in html
    assert "CUIT 20123456786" in html
    assert reverse("clientes:detalle", args=[cliente_existente.pk]) in html


def test_cliente_inactivo(cliente_autenticado, cliente_existente):
    Cliente.objects.filter(pk=cliente_existente.pk).update(activo=False)

    respuesta = cliente_autenticado.get(url(cliente_existente))

    assert respuesta.status_code == 302
    assert respuesta.url == reverse("clientes:buscar")
    seguida = cliente_autenticado.get(respuesta.url)
    assert "El cliente no está disponible." in seguida.content.decode()


def test_cliente_inexistente_404(cliente_autenticado):
    respuesta = cliente_autenticado.get(reverse("clientes:historial", args=[999999]))

    assert respuesta.status_code == 404


def test_requiere_sesion(cliente_existente):
    respuesta = Client().get(url(cliente_existente))

    assert respuesta.status_code == 302
    assert respuesta.url.startswith(reverse(settings.LOGIN_URL))


def test_historial_solo_lectura(cliente_autenticado, cliente_existente, muestra_de, estudio_en):
    estudio_en(muestra_de(cliente_existente, date(2026, 10, 1), 200001), con_informe=True)
    antes = (Muestra.objects.count(), Estudio.objects.count(), Informe.objects.count())

    respuesta = cliente_autenticado.post(url(cliente_existente), {"estado": "finalizado"})

    assert respuesta.status_code == 405
    assert (Muestra.objects.count(), Estudio.objects.count(), Informe.objects.count()) == antes


def test_consultas_acotadas(cliente_autenticado, cliente_existente, otro, muestra_de, estudio_en):
    estudio_en(muestra_de(otro, date(2026, 10, 1), 300000), con_informe=True)
    for i in range(100):
        muestra = muestra_de(cliente_existente, date(2026, 1, 1), 200001 + i)
        estudio_en(muestra, con_informe=True)

    def consultas(cliente):
        with CaptureQueriesContext(connection) as capturadas:
            assert cliente_autenticado.get(url(cliente)).status_code == 200
        return len(capturadas)

    consultas(otro)  # calienta caché de sesión y contenttypes
    assert consultas(cliente_existente) == consultas(otro)


# --- US2: filtros ----------------------------------------------------------------------------


def test_formulario_de_filtros(cliente_autenticado, cliente_existente, muestra_de):
    muestra_de(cliente_existente, date(2026, 10, 1), 200001)

    html = html_de(cliente_autenticado, cliente_existente, desde="2026-10-01", estado="en_proceso")

    for etiqueta in ("Ingreso desde", "Ingreso hasta", "Estado del estudio", "Todos"):
        assert etiqueta in html
    for _, texto in EstadoEstudio.choices:
        assert texto in html
    assert 'value="2026-10-01"' in html
    assert re.search(r'<option value="en_proceso"[^>]*selected', html)


@pytest.mark.parametrize(
    ("parametros", "error"),
    [
        (
            {"desde": "2026-10-20", "hasta": "2026-10-01"},
            "La fecha desde no puede ser posterior a la fecha hasta.",
        ),
        ({"desde": "31/02/2026"}, "Ingresá una fecha válida (dd/mm/aaaa)."),
        ({"estado": "otro"}, "Elegí un estado de la lista."),
    ],
)
def test_filtros_invalidos(cliente_autenticado, cliente_existente, muestra_de, parametros, error):
    muestra_de(cliente_existente, date(2026, 9, 1), 200001)
    muestra_de(cliente_existente, date(2026, 10, 10), 200002)

    html = html_de(cliente_autenticado, cliente_existente, **parametros)

    assert error in html
    assert muestras_en(html) == [200002, 200001]
    assert "Limpiar filtros" in html


def test_sin_coincidencias(cliente_autenticado, cliente_existente, muestra_de):
    muestra_de(cliente_existente, date(2026, 9, 1), 200001)

    html = html_de(cliente_autenticado, cliente_existente, desde="2026-10-01")

    assert "Ninguna muestra coincide con los filtros." in html
    assert "Este cliente no tiene muestras registradas." not in html
    assert f'href="{url(cliente_existente)}"' in html
    assert "Limpiar filtros" in html


@pytest.mark.parametrize(
    ("parametros", "ofrece"),
    [
        ({}, False),
        ({"desde": "", "hasta": "", "estado": ""}, False),
        ({"estado": "finalizado"}, True),
        ({"hasta": "fecha-mal"}, True),
    ],
)
def test_limpiar_filtros_solo_con_filtros(
    cliente_autenticado, cliente_existente, muestra_de, estudio_en, parametros, ofrece
):
    estudio_en(muestra_de(cliente_existente, date(2026, 10, 1), 200001), EstadoEstudio.FINALIZADO)

    html = html_de(cliente_autenticado, cliente_existente, **parametros)

    assert ("Limpiar filtros" in html) is ofrece


def test_paginacion_conserva_filtros(
    cliente_autenticado, cliente_existente, muestra_de, estudio_en
):
    for i in range(25):
        muestra = muestra_de(cliente_existente, date(2026, 10, 2), 200001 + i)
        estudio_en(muestra)
    con_tres = Muestra.objects.get(numero_pi=200025)
    estudio_en(con_tres, tipo="Efluente")
    estudio_en(con_tres, tipo="Pileta")
    filtros = {"estado": "pendiente_analisis", "desde": "2026-10-01"}

    pagina_1 = html_de(cliente_autenticado, cliente_existente, **filtros)

    assert len(muestras_en(pagina_1)) == 20
    assert len(estudios_en(pagina_1)) == 22
    siguiente = re.search(r'href="\?([^"]*page=2)"', pagina_1).group(1).replace("&amp;", "&")
    assert "estado=pendiente_analisis" in siguiente
    assert "desde=2026-10-01" in siguiente
    pagina_2 = html_de(cliente_autenticado, cliente_existente, **filtros, page=2)
    assert len(muestras_en(pagina_2)) == 5


# --- US3: detalle del estudio, de la muestra e informe ---------------------------------------


def test_enlaces_a_detalles(cliente_autenticado, cliente_existente, muestra_de, estudio_en):
    muestra = muestra_de(cliente_existente, date(2026, 10, 1), 200001)
    estudio = estudio_en(muestra, EstadoEstudio.EN_PROCESO)

    html = html_de(cliente_autenticado, cliente_existente)

    url_muestra = reverse("muestras:detalle", args=[muestra.pk])
    url_estudio = reverse("estudios:detalle", args=[estudio.pk])
    assert f'href="{url_muestra}"' in html
    assert f'href="{url_estudio}"' in html
    assert cliente_autenticado.get(url_muestra).status_code == 200
    assert cliente_autenticado.get(url_estudio).status_code == 200


def test_ver_informe_solo_con_informe(
    cliente_autenticado, cliente_existente, muestra_de, estudio_en
):
    muestra = muestra_de(cliente_existente, date(2026, 10, 1), 200001)
    con_informe = estudio_en(muestra, con_informe=True)
    en_proceso = estudio_en(muestra, EstadoEstudio.EN_PROCESO, tipo="Efluente")
    inconsistente = estudio_en(muestra, EstadoEstudio.INFORME_GENERADO, tipo="Pileta")

    html = html_de(cliente_autenticado, cliente_existente)

    assert html.count("Ver informe") == 1
    assert "Ver informe INF-000001" in html
    assert f'href="{reverse("informes:ver", args=[con_informe.pk])}"' in html
    for sin_informe in (en_proceso, inconsistente):
        assert reverse("informes:ver", args=[sin_informe.pk]) not in html
