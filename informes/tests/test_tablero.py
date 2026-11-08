"""Tests de los cálculos del dashboard (US 8.3): `informes/tablero.py`."""

import datetime as dt
import io
from decimal import Decimal

import pytest
from django.utils import timezone

from estudios import demo
from estudios.models import EstadoEstudio, Estudio
from estudios.tests.utiles import asignacion_de, cargar, validar
from informes import tablero
from informes.servicios import emitir_informe
from muestras.models import Muestra

pytestmark = pytest.mark.django_db

D = dt.date


def momento(fecha, hora=10, minuto=0):
    """Datetime con la zona del laboratorio."""
    return timezone.make_aware(dt.datetime(fecha.year, fecha.month, fecha.day, hora, minuto))


@pytest.fixture
def armar(otra_muestra, estudio_para, completar, bioquimico):
    """`armar(ingreso, creacion=None, emision=None, codigos=("PH",))` → estudio con esas fechas.

    La muestra ingresa en `ingreso`; el estudio se crea en `creacion` (o el día de ingreso) y, con
    `emision`, se completa y se emite su informe en ese momento.
    """
    numeros = iter(range(300001, 400000))

    def crear(ingreso, creacion=None, emision=None, codigos=("PH",), cliente_activo=True):
        numero = next(numeros)
        muestra = otra_muestra(numero, f"Cliente {numero}", str(10000000 + numero % 10000000))
        Muestra.objects.filter(pk=muestra.pk).update(fecha_ingreso=ingreso, fecha_muestreo=ingreso)
        if not cliente_activo:
            muestra.cliente.__class__.objects.filter(pk=muestra.cliente_id).update(activo=False)
        muestra.refresh_from_db()
        with demo.reloj(creacion or momento(ingreso)):
            estudio = estudio_para(muestra, *codigos)
        if emision is not None:
            completar(estudio)
            with demo.reloj(emision):
                emitir_informe(estudio.pk, bioquimico)
        return Estudio.objects.get(pk=estudio.pk)

    return crear


# --- Períodos y variación (T005) ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("clave", "hoy", "esperado"),
    [
        (
            "este_mes",
            D(2026, 11, 8),
            (D(2026, 11, 1), D(2026, 11, 8), D(2026, 10, 1), D(2026, 10, 8)),
        ),
        (
            "este_mes",
            D(2026, 11, 1),
            (D(2026, 11, 1), D(2026, 11, 1), D(2026, 10, 1), D(2026, 10, 1)),
        ),
        (
            "este_mes",
            D(2026, 3, 31),
            (D(2026, 3, 1), D(2026, 3, 31), D(2026, 2, 1), D(2026, 2, 28)),
        ),
        (
            "este_mes",
            D(2028, 3, 31),
            (D(2028, 3, 1), D(2028, 3, 31), D(2028, 2, 1), D(2028, 2, 29)),
        ),
        (
            "este_mes",
            D(2026, 1, 15),
            (D(2026, 1, 1), D(2026, 1, 15), D(2025, 12, 1), D(2025, 12, 15)),
        ),
        (
            "mes_anterior",
            D(2026, 11, 8),
            (D(2026, 10, 1), D(2026, 10, 31), D(2026, 9, 1), D(2026, 9, 30)),
        ),
        (
            "ultimos_3",
            D(2026, 11, 8),
            (D(2026, 9, 1), D(2026, 11, 8), D(2026, 6, 1), D(2026, 8, 8)),
        ),
        (
            "ultimos_6",
            D(2026, 11, 8),
            (D(2026, 6, 1), D(2026, 11, 8), D(2025, 12, 1), D(2026, 5, 8)),
        ),
        (
            "ultimos_3",
            D(2026, 5, 31),
            (D(2026, 3, 1), D(2026, 5, 31), D(2025, 12, 1), D(2026, 2, 28)),
        ),
        ("xyz", D(2026, 11, 8), (D(2026, 11, 1), D(2026, 11, 8), D(2026, 10, 1), D(2026, 10, 8))),
    ],
)
def test_periodos(clave, hoy, esperado):
    periodo = tablero.periodo(clave, hoy)
    assert (periodo.inicio, periodo.fin, periodo.inicio_anterior, periodo.fin_anterior) == esperado
    assert periodo.clave in tablero.PERIODOS
    if clave == "xyz":
        assert periodo.clave == "este_mes"


@pytest.mark.parametrize(
    ("actual", "anterior", "favorable_si_sube", "esperado"),
    [
        (10, 8, True, (2, 25, "sube", "▲", "exito")),
        (8, 10, True, (-2, -20, "baja", "▼", "peligro")),
        (5, 5, True, (0, 0, "igual", "=", "neutro")),
        (3, 0, True, (3, None, "sube", "▲", "exito")),
        (0, 0, True, (0, None, "igual", "=", "neutro")),
        (Decimal("12.5"), Decimal("10.0"), False, (Decimal("2.5"), 25, "sube", "▲", "peligro")),
        (Decimal("8.0"), Decimal("10.0"), False, (Decimal("-2.0"), -20, "baja", "▼", "exito")),
    ],
)
def test_variacion(actual, anterior, favorable_si_sube, esperado):
    variacion = tablero.variacion(actual, anterior, favorable_si_sube=favorable_si_sube)
    assert (
        variacion.diferencia,
        variacion.porcentaje,
        variacion.sentido,
        variacion.simbolo,
        variacion.tono,
    ) == esperado


def test_variacion_sin_valores():
    assert tablero.variacion(None, Decimal("3.0"), favorable_si_sube=False) is None
    assert tablero.variacion(Decimal("3.0"), None, favorable_si_sube=False) is None


# --- US1: indicadores y estados ----------------------------------------------------------------


def test_indicadores_cuentan_por_fecha(armar, estudio_para):
    hoy = D(2026, 11, 8)
    # Período: 1–8/11; anterior: 1–8/10.
    est = armar(D(2026, 11, 3), emision=momento(D(2026, 11, 6)))
    with demo.reloj(momento(D(2026, 11, 3))):
        estudio_para(
            est.muestra, "PH"
        )  # segundo estudio de la misma muestra: 1 muestra, 2 estudios
    armar(D(2026, 11, 8))
    armar(D(2026, 10, 5), emision=momento(D(2026, 10, 7)))
    armar(D(2026, 10, 20))  # fuera de los dos tramos
    armar(D(2026, 11, 2), cliente_activo=False)  # clientes inactivos cuentan igual
    indicadores = tablero.indicadores(tablero.periodo("este_mes", hoy))
    assert (indicadores["muestras"].actual, indicadores["muestras"].anterior) == (3, 1)
    assert (indicadores["estudios"].actual, indicadores["estudios"].anterior) == (4, 1)
    assert (indicadores["informes"].actual, indicadores["informes"].anterior) == (1, 1)
    assert indicadores["muestras"].variacion.diferencia == 2


def test_estudios_creados_por_fecha(armar):
    hoy = D(2026, 11, 8)
    armar(D(2026, 10, 30), creacion=momento(D(2026, 11, 2)))
    armar(D(2026, 11, 4))
    indicadores = tablero.indicadores(tablero.periodo("este_mes", hoy))
    assert indicadores["estudios"].actual == 2
    assert indicadores["muestras"].actual == 1


def test_estudios_por_estado(armar):
    armar(D(2026, 11, 3))
    armar(D(2026, 11, 3), emision=momento(D(2026, 11, 5)))
    estudio = armar(D(2026, 11, 4))
    Estudio.objects.filter(pk=estudio.pk).update(estado=EstadoEstudio.FINALIZADO)
    estados = {etiqueta: total for etiqueta, total, _ in tablero.estudios_por_estado()}
    assert estados == {
        "Pendiente de análisis": 1,
        "En proceso": 0,
        "Finalizado": 1,
        "Informe generado": 1,
    }


def test_zona_horaria(armar):
    # 31/10 23:30 en Argentina es 1/11 02:30 UTC: cuenta en octubre.
    armar(D(2026, 10, 30), emision=momento(D(2026, 10, 31), 23, 30))
    octubre = tablero.indicadores(tablero.periodo("mes_anterior", D(2026, 11, 8)))
    noviembre = tablero.indicadores(tablero.periodo("este_mes", D(2026, 11, 8)))
    assert octubre["informes"].actual == 1
    assert noviembre["informes"].actual == 0


# --- US2: tiempo de respuesta y series ---------------------------------------------------------


def test_tiempo_de_respuesta(armar):
    armar(D(2026, 10, 1), emision=momento(D(2026, 10, 11)))  # 10 días
    armar(D(2026, 10, 1), emision=momento(D(2026, 10, 14)))  # 13 días
    armar(D(2026, 9, 1), emision=momento(D(2026, 9, 9)))  # 8 días
    assert tablero.tiempo_respuesta(D(2026, 10, 1), D(2026, 10, 31)) == Decimal("11.5")
    assert tablero.tiempo_respuesta(D(2026, 9, 1), D(2026, 9, 30)) == Decimal("8.0")
    assert tablero.tiempo_respuesta(D(2026, 8, 1), D(2026, 8, 31)) is None
    respuesta = tablero.indicadores(tablero.periodo("mes_anterior", D(2026, 11, 8)))["respuesta"]
    assert (respuesta.actual, respuesta.anterior) == (Decimal("11.5"), Decimal("8.0"))
    assert respuesta.variacion.tono == "peligro"


def test_series_fijas(armar):
    hoy = D(2026, 11, 8)
    armar(D(2026, 11, 2), emision=momento(D(2026, 11, 4)))  # semana del 2/11, 2 días
    armar(D(2026, 10, 1), emision=momento(D(2026, 10, 11)))  # 10 días
    armar(D(2026, 8, 18))  # semana del 17/8 (12.ª hacia atrás)
    armar(D(2026, 8, 10))  # semana anterior a la ventana: no aparece
    mensual = tablero.serie_mensual(hoy)
    assert [m["etiqueta"] for m in mensual] == [
        "jun 2026",
        "jul 2026",
        "ago 2026",
        "sep 2026",
        "oct 2026",
        "nov 2026",
    ]
    assert [m["dias"] for m in mensual] == [None, None, None, None, Decimal("10.0"), Decimal("2.0")]
    semanal = tablero.serie_semanal(hoy)
    assert len(semanal) == 12
    assert semanal[0]["desde"] == D(2026, 8, 17)
    assert semanal[-1]["desde"] == D(2026, 11, 2)
    assert (semanal[0]["muestras"], semanal[0]["informes"]) == (1, 0)
    assert (semanal[-1]["muestras"], semanal[-1]["informes"]) == (1, 1)
    assert sum(s["muestras"] for s in semanal) == 3
    # No dependen del período: son funciones solo de `hoy`.


# --- US3: alertas ------------------------------------------------------------------------------


def test_sin_avanzar(armar, empleado, bioquimico):
    ahora = momento(D(2026, 11, 8), 12)
    viejo = armar(D(2026, 10, 25), creacion=momento(D(2026, 10, 25)))  # 14 días sin actividad
    mas_viejo = armar(D(2026, 10, 20), creacion=momento(D(2026, 10, 20)))
    reciente = armar(D(2026, 11, 6), creacion=momento(D(2026, 11, 6)))
    con_carga = armar(D(2026, 10, 20), creacion=momento(D(2026, 10, 20)), codigos=("PH", "CL-"))
    with demo.reloj(momento(D(2026, 11, 5))):
        cargar(con_carga, empleado, PH="7.4")
    con_correccion = armar(D(2026, 10, 1), creacion=momento(D(2026, 10, 1)), codigos=("PH", "CL-"))
    with demo.reloj(momento(D(2026, 10, 2))):
        cargar(con_correccion, empleado, PH="7.4")
    from estudios.servicios import corregir_mediciones

    asignacion = asignacion_de(con_correccion, "PH")
    with demo.reloj(momento(D(2026, 11, 4))):
        corregir_mediciones(
            con_correccion.pk,
            {asignacion.pk: (str(asignacion.medicion.valor_ingresado), Decimal("7.5"))},
            empleado,
        )
    con_validacion = armar(D(2026, 10, 1), creacion=momento(D(2026, 10, 1)), codigos=("PH", "CL-"))
    with demo.reloj(momento(D(2026, 10, 2))):
        cargar(con_validacion, empleado, PH="7.4", CL_="4")
    with demo.reloj(momento(D(2026, 11, 3))):
        validar(con_validacion, bioquimico, "PH")
    armar(D(2026, 10, 1), emision=momento(D(2026, 10, 5)))  # con informe: no es alerta

    alertas = tablero.alertas(ahora)
    filas = alertas["sin_avanzar"]
    assert [f["estudio"].pk for f in filas] == [mas_viejo.pk, viejo.pk]
    assert [f["dias"] for f in filas] == [19, 14]
    excluidos = {reciente.pk, con_carga.pk, con_correccion.pk, con_validacion.pk}
    assert not excluidos & {f["estudio"].pk for f in filas}


def test_finalizados_sin_informe(armar, empleado, bioquimico):
    ahora = momento(D(2026, 11, 8), 12)
    finalizado = armar(D(2026, 10, 1), codigos=("PH",))
    with demo.reloj(momento(D(2026, 10, 2))):
        cargar(finalizado, empleado, PH="7.4")
    with demo.reloj(momento(D(2026, 10, 28))):
        validar(finalizado, bioquimico, "PH")
    armar(D(2026, 10, 1), emision=momento(D(2026, 10, 5)))
    filas = tablero.alertas(ahora)["finalizados_sin_informe"]
    assert [(f["estudio"].pk, f["dias"]) for f in filas] == [(finalizado.pk, 11)]
    assert not tablero.alertas(ahora)["sin_avanzar"]


def test_alertas_con_la_demo(catalogo):
    hoy = timezone.localtime()
    ahora = hoy.replace(day=2, hour=12, minute=0, second=0, microsecond=0)
    if ahora > hoy:
        ahora = (ahora.replace(day=1) - dt.timedelta(days=1)).replace(day=2)
    demo.cargar_demo(io.StringIO(), ahora=ahora)
    alertas = tablero.alertas(ahora)
    sin_avanzar = {f["estudio"].muestra.origen.nombre for f in alertas["sin_avanzar"]}
    finalizados = {f["estudio"].muestra.origen.nombre for f in alertas["finalizados_sin_informe"]}
    assert "Pozo domiciliario" in sin_avanzar
    assert "Escuela N° 12" in finalizados
