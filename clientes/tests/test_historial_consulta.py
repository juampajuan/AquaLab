"""Consulta del historial del cliente (US 3.3), sin HTTP."""

from datetime import date

import pytest
from django.template import Context, Template

from clientes.historial import muestras_del_historial
from clientes.models import Cliente
from estudios.models import EstadoEstudio

pytestmark = pytest.mark.django_db


@pytest.fixture
def otro(db):
    return Cliente.objects.create(
        nombre="Otra Persona", tipo_documento="DNI", numero_documento="27999888", email="o@x.com"
    )


def numeros(muestras):
    return [m.numero_pi for m in muestras]


def test_solo_muestras_del_cliente(cliente_existente, otro, muestra_de):
    muestra_de(cliente_existente, date(2026, 10, 1), 200001)
    muestra_de(otro, date(2026, 10, 2), 200002)

    assert numeros(muestras_del_historial(cliente_existente)) == [200001]


def test_orden_del_historial(cliente_existente, muestra_de, estudio_en):
    muestra_de(cliente_existente, date(2026, 9, 15), 200001)
    m_octubre = muestra_de(cliente_existente, date(2026, 10, 10), 200002)
    muestra_de(cliente_existente, date(2026, 10, 25), 200003)
    muestra_de(cliente_existente, date(2026, 10, 25), 200004)
    primero = estudio_en(m_octubre)
    segundo = estudio_en(m_octubre, tipo="Efluente")

    historial = list(muestras_del_historial(cliente_existente))

    assert numeros(historial) == [200004, 200003, 200002, 200001]
    assert [e.pk for e in historial[2].estudios_historial] == [segundo.pk, primero.pk]


def test_trae_estudios_e_informe(
    cliente_existente, muestra_de, estudio_en, django_assert_num_queries
):
    con_estudio = muestra_de(cliente_existente, date(2026, 10, 1), 200001)
    muestra_de(cliente_existente, date(2026, 9, 1), 200002)
    estudio_en(con_estudio, con_informe=True)

    historial = list(muestras_del_historial(cliente_existente))

    with django_assert_num_queries(0):
        estudio = historial[0].estudios_historial[0]
        assert estudio.informe.numero_mostrado == "INF-000001"
        assert historial[1].estudios_historial == []


def test_sin_informe_no_consulta(
    cliente_existente, muestra_de, estudio_en, django_assert_num_queries
):
    estudio_en(muestra_de(cliente_existente, date(2026, 10, 1), 200001))
    estudio = list(muestras_del_historial(cliente_existente))[0].estudios_historial[0]
    plantilla = Template("{% if estudio.informe %}con{% else %}sin{% endif %}")

    with django_assert_num_queries(0):
        assert plantilla.render(Context({"estudio": estudio})) == "sin"


@pytest.mark.parametrize(
    ("desde", "hasta", "esperados"),
    [
        (date(2026, 10, 1), None, [200003, 200002]),
        (None, date(2026, 10, 1), [200002, 200001]),
        (date(2026, 10, 1), date(2026, 10, 1), [200002]),
        (date(2026, 9, 15), date(2026, 10, 20), [200003, 200002, 200001]),
    ],
)
def test_filtro_fechas(cliente_existente, muestra_de, desde, hasta, esperados):
    muestra_de(cliente_existente, date(2026, 9, 15), 200001)
    muestra_de(cliente_existente, date(2026, 10, 1), 200002)
    muestra_de(cliente_existente, date(2026, 10, 20), 200003)

    assert numeros(muestras_del_historial(cliente_existente, desde, hasta)) == esperados


def test_filtro_estado(cliente_existente, muestra_de, estudio_en):
    mixta = muestra_de(cliente_existente, date(2026, 10, 1), 200001)
    pendiente = muestra_de(cliente_existente, date(2026, 10, 2), 200002)
    en_proceso = estudio_en(mixta, EstadoEstudio.EN_PROCESO)
    estudio_en(mixta, EstadoEstudio.FINALIZADO, tipo="Efluente")
    estudio_en(mixta, EstadoEstudio.EN_PROCESO, tipo="Pileta")
    estudio_en(pendiente)

    historial = list(muestras_del_historial(cliente_existente, estado=EstadoEstudio.EN_PROCESO))

    assert numeros(historial) == [200001]
    estados = {e.estado for e in historial[0].estudios_historial}
    assert estados == {EstadoEstudio.EN_PROCESO}
    assert en_proceso.pk in [e.pk for e in historial[0].estudios_historial]
    assert len(historial[0].estudios_historial) == 2


def test_filtros_combinados(cliente_existente, muestra_de, estudio_en):
    vieja = muestra_de(cliente_existente, date(2026, 9, 1), 200001)
    nueva = muestra_de(cliente_existente, date(2026, 10, 15), 200002)
    otra = muestra_de(cliente_existente, date(2026, 10, 16), 200003)
    estudio_en(vieja, con_informe=True)
    estudio_en(nueva, con_informe=True)
    estudio_en(otra, EstadoEstudio.EN_PROCESO)

    historial = muestras_del_historial(
        cliente_existente, desde=date(2026, 10, 1), estado=EstadoEstudio.INFORME_GENERADO
    )

    assert numeros(historial) == [200002]
