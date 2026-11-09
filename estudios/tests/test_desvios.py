"""Regla y detección de desvíos al vuelo (US 8.2): `estudios/desvios.py`."""

import datetime as dt
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from estudios import desvios
from estudios.comparacion import HistorialPrueba, Punto, numero
from estudios.desvios import HISTORIAL_INSUFICIENTE, Deteccion, Regla
from estudios.mediciones import es_presencia, texto_presencia
from estudios.models import EstadoPruebaEstudio, Estudio, PruebaEstudio, Resultado, Validacion
from estudios.servicios import corregir_mediciones
from estudios.tests.conftest import en_grupo_bioquimicos
from estudios.tests.utiles import asignacion_de, validar
from muestras.models import Origen
from pruebas.limites import Evaluacion

DIA = dt.date(2026, 3, 1)
REGLA = Regla(Decimal("30"), 3)


def dia(n):
    return DIA + dt.timedelta(days=n)


# --- Regla pura (sin base) -------------------------------------------------------------------


def punto(valor, n, unidad="mg/l", *, referencia=False):
    valor = Decimal(valor)
    return Punto(
        fecha_muestreo=dia(n),
        numero_pi=300000 + n,
        muestra_pk=n,
        estudio_pk=n,
        valor=valor,
        texto=texto_presencia(valor) if es_presencia(unidad) else numero(valor),
        unidad=unidad,
        tipo_vertido="agua",
        validado=not referencia,
        evaluacion=Evaluacion.CUMPLE,
        es_referencia=referencia,
    )


def historial(anteriores, valor, unidad="mg/l"):
    return HistorialPrueba(
        prueba=None,
        presencia=es_presencia(unidad),
        unidad=unidad,
        referencia=punto(valor, 99, unidad, referencia=True),
        anteriores=tuple(punto(v, n, unidad) for n, v in enumerate(anteriores)),
    )


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [("143", False), ("77", False), ("143.5", True), ("76.9", True), ("110", False)],
)
def test_es_desvio_bordes(valor, esperado):
    assert desvios.es_desvio(Decimal(valor), Decimal(110), Decimal(30)) is esperado


def test_mediana_cero():
    assert desvios.es_desvio(Decimal(5), Decimal(0), Decimal(30)) is True
    assert desvios.es_desvio(Decimal(0), Decimal(0), Decimal(30)) is False
    deteccion = desvios.detectar(historial(["0", "0", "0"], "5"), REGLA)
    assert deteccion.porcentaje is None
    assert deteccion.variacion_texto == "▲ +5 mg/l, sin porcentaje (mediana previa 0)"


def test_presencia():
    deteccion = desvios.detectar(historial(["0", "0", "0"], "1", "A/P"), REGLA)
    assert deteccion.presencia and deteccion.referencia == 0 and deteccion.porcentaje is None
    assert deteccion.observado == "Presente"
    assert deteccion.referencia_texto == "Ausente"
    assert deteccion.etiqueta_referencia == "Últimos 3"
    assert deteccion.variacion_texto == "Presente (los últimos 3: Ausente)"
    assert desvios.detectar(historial(["0", "0", "1"], "1", "A/P"), REGLA) is None
    assert desvios.detectar(historial(["0", "0", "0"], "0", "A/P"), REGLA) is None
    al_reves = desvios.detectar(historial(["1", "1", "1"], "0", "A/P"), REGLA)
    assert al_reves.referencia == 1
    assert al_reves.variacion_texto == "Ausente (los últimos 3: Presente)"


def test_mediana_de_los_ultimos_n():
    deteccion = desvios.detectar(historial(["50", "60", "100", "110", "120"], "160"), REGLA)
    assert deteccion.referencia == Decimal(110)
    assert deteccion.porcentaje == Decimal("45.5")
    assert [p.valor for p in deteccion.previos] == [Decimal(100), Decimal(110), Decimal(120)]
    assert deteccion.observado == "160 mg/l"
    assert deteccion.etiqueta_referencia == "Mediana de los últimos 3"
    assert deteccion.referencia_texto == "110 mg/l"
    assert deteccion.variacion_texto == "▲ +50 mg/l (+45,5 %)"
    assert deteccion.umbral_texto == "30 %"


def test_mediana():
    assert desvios.mediana([Decimal(14), Decimal("4.1"), Decimal("4.3")]) == Decimal("4.3")
    assert desvios.mediana([Decimal(4), Decimal(1), Decimal(3), Decimal(2)]) == Decimal("2.5")
    assert desvios.mediana([Decimal(7)]) == Decimal(7)


def test_un_pico_aislado_no_contamina():
    """Caso de la demo (Detergentes de Colectora): 4,2 contra 14 / 4,1 / 4,3. Con el promedio
    (7,4667) sería −43,8 %; con la mediana (4,3) es −2,3 % y no hay desvío."""
    assert desvios.detectar(historial(["14", "4.1", "4.3"], "4.2"), REGLA) is None
    # Al revés, el pico es el resultado actual: sí es desvío contra la mediana.
    deteccion = desvios.detectar(historial(["4.1", "4.3", "4.2"], "14"), REGLA)
    assert deteccion.referencia == Decimal("4.2")
    assert deteccion.porcentaje == Decimal("233.3")


def test_mediana_con_cantidad_par():
    regla = Regla(Decimal("30"), 4)
    deteccion = desvios.detectar(historial(["100", "100", "120", "200"], "160"), regla)
    assert deteccion.referencia == Decimal(110)
    assert deteccion.etiqueta_referencia == "Mediana de los últimos 4"
    assert desvios.detectar(historial(["100", "100", "120", "200"], "140"), regla) is None


def test_desvio_para_abajo():
    deteccion = desvios.detectar(historial(["100", "110", "120"], "50"), REGLA)
    assert deteccion.variacion_texto == "▼ -60 mg/l (-54,5 %)"


def test_historial_insuficiente():
    h = historial(["100", "110"], "500")
    assert desvios.detectar(h, REGLA) is None
    assert desvios.historial_suficiente(h, REGLA) is False
    assert desvios.historial_suficiente(historial(["1", "1", "1"], "5"), REGLA) is True


def test_sin_referencia():
    h = HistorialPrueba(prueba=None, presencia=False, unidad="mg/l", anteriores=(punto("1", 0),))
    assert desvios.detectar(h, REGLA) is None


def test_regla():
    assert desvios.regla() == Regla(Decimal("30"), 3)
    assert desvios.texto_regla(desvios.regla()) == (
        "más de un 30 % respecto de la mediana de los últimos 3 resultados validados del origen"
    )


# --- Con servicios reales --------------------------------------------------------------------


@pytest.fixture
def origen(cliente_a):
    return Origen.objects.create(cliente=cliente_a, nombre="Pozo de desvíos")


@pytest.fixture
def historia_cloruro(origen, estudio_en_origen):
    """Cloruro validado 100, 110 y 120 mg/l los días 0, 1 y 2."""
    for n, valor in enumerate(["10", "11", "12"]):
        estudio_en_origen(origen, dia(n), 300301 + n, {"CL-": valor})


def evaluacion_de(estudio, codigo="CL-"):
    asignacion = asignacion_de(estudio, codigo)
    asignaciones = list(
        estudio.pruebas_asignadas.select_related("prueba", "resultado").filter(
            estado=EstadoPruebaEstudio.CARGADA
        )
    )
    return desvios.evaluar_estudio(estudio, asignaciones).get(asignacion.pk, "ausente")


@pytest.mark.django_db
def test_evaluar_estudio(origen, historia_cloruro, estudio_en_origen):
    con_desvio = estudio_en_origen(origen, dia(3), 300310, {"CL-": "16"}, validar_todo=False)
    deteccion = evaluacion_de(con_desvio)
    assert isinstance(deteccion, Deteccion)
    assert deteccion.valor == Decimal(160) and deteccion.referencia == Decimal(110)
    assert deteccion.porcentaje == Decimal("45.5")
    assert [p.numero_pi for p in deteccion.previos] == [300301, 300302, 300303]

    dentro = estudio_en_origen(origen, dia(4), 300311, {"CL-": "14.3"}, validar_todo=False)
    assert evaluacion_de(dentro) is None

    sin_resultado = estudio_en_origen(origen, dia(5), 300312, {"CL-": None})
    assert evaluacion_de(sin_resultado) == "ausente"


@pytest.mark.django_db
def test_historial_insuficiente_con_servicios(origen, estudio_en_origen):
    estudio_en_origen(origen, dia(0), 300301, {"CL-": "10"})
    estudio_en_origen(origen, dia(1), 300302, {"CL-": "11"})
    actual = estudio_en_origen(origen, dia(2), 300303, {"CL-": "90"}, validar_todo=False)
    assert evaluacion_de(actual) == HISTORIAL_INSUFICIENTE


@pytest.mark.django_db
def test_dependiente(origen, estudio_en_origen, pruebas_division, empleado):
    for n in range(3):
        previo = estudio_en_origen(
            origen, dia(n), 300301 + n, {"DIV-A": "20", "DIV-B": "2", "DIV": None}
        )
        validar(previo, en_grupo_bioquimicos(empleado), "DIV")
    actual = estudio_en_origen(
        origen, dia(3), 300310, {"DIV-A": "30", "DIV-B": "2", "DIV": None}, validar_todo=False
    )
    deteccion = evaluacion_de(actual, "DIV")
    assert deteccion.valor == Decimal(15) and deteccion.referencia == Decimal(10)
    assert deteccion.porcentaje == Decimal("50.0")


@pytest.mark.django_db
def test_correccion_se_refleja(origen, historia_cloruro, estudio_en_origen, empleado):
    actual = estudio_en_origen(origen, dia(3), 300310, {"CL-": "16"}, validar_todo=False)
    cl = asignacion_de(actual, "CL-")
    assert isinstance(evaluacion_de(actual), Deteccion)

    corregir_mediciones(actual.pk, {cl.pk: (Decimal("16"), Decimal("11.5"))}, empleado)
    assert evaluacion_de(actual) is None

    corregir_mediciones(actual.pk, {cl.pk: (Decimal("11.5"), Decimal("20"))}, empleado)
    deteccion = evaluacion_de(actual)
    assert deteccion.valor == Decimal(200)

    corregir_mediciones(actual.pk, {cl.pk: (Decimal("20"), None)}, empleado)
    assert evaluacion_de(actual) == "ausente"


@pytest.mark.django_db
def test_usa_historial_de_la_comparacion(origen, cliente_a, estudio_en_origen, empleado, catalogo):
    otro = Origen.objects.create(cliente=cliente_a, nombre="Otro pozo")
    estudio_en_origen(origen, dia(0), 300301, {"CL-": "10"})
    estudio_en_origen(origen, dia(1), 300302, {"CL-": "11"})
    estudio_en_origen(origen, dia(2), 300303, {"CL-": "12"}, validar_todo=False)  # sin validar
    anulado = estudio_en_origen(origen, dia(3), 300304, {"CL-": "12"})
    cl = asignacion_de(anulado, "CL-")
    corregir_mediciones(anulado.pk, {cl.pk: (Decimal("12"), Decimal("12.5"))}, empleado)
    estudio_en_origen(otro, dia(4), 300305, {"CL-": "12"})  # otro origen
    estudio_en_origen(origen, dia(9), 300306, {"CL-": "12"})  # muestra posterior
    actual = estudio_en_origen(origen, dia(5), 300307, {"CL-": "40"}, validar_todo=False)

    assert evaluacion_de(actual) == HISTORIAL_INSUFICIENTE


@pytest.mark.django_db
def test_estudio_de_muestra_antigua(origen, estudio_en_origen):
    for n in range(3):
        estudio_en_origen(origen, dia(40 + n), 300301 + n, {"CL-": "10"})
    antiguo = estudio_en_origen(origen, dia(0), 300310, {"CL-": "40"}, validar_todo=False)
    assert evaluacion_de(antiguo) == HISTORIAL_INSUFICIENTE


@pytest.mark.django_db
def test_calcular_no_escribe(origen, historia_cloruro, estudio_en_origen):
    actual = estudio_en_origen(origen, dia(3), 300310, {"CL-": "16"}, validar_todo=False)

    def estado():
        return (
            Validacion.objects.count(),
            list(Resultado.objects.values_list("pk", "valor", "fecha_calculo").order_by("pk")),
            list(PruebaEstudio.objects.values_list("pk", "estado").order_by("pk")),
            list(Estudio.objects.values_list("pk", "estado").order_by("pk")),
        )

    antes = estado()
    with CaptureQueriesContext(connection) as consultas:
        evaluacion_de(actual)
        desvios.pendientes()
    assert estado() == antes
    escrituras = ("INSERT", "UPDATE", "DELETE")
    assert not [q for q in consultas.captured_queries if q["sql"].lstrip().startswith(escrituras)]


@pytest.mark.django_db
def test_consultas_evaluar_estudio(origen, estudio_en_origen):
    codigos = ["CL-", "PH", "COND", "TURBIDEZ", "OD", "SST"]
    pocos = {"CL-": "10"}
    muchos = {c: "10" for c in codigos}
    for n in range(3):
        estudio_en_origen(origen, dia(n), 300301 + n, muchos)

    def contar(valores, numero_pi):
        estudio = estudio_en_origen(origen, dia(5), numero_pi, valores, validar_todo=False)
        asignaciones = list(estudio.pruebas_asignadas.select_related("prueba", "resultado"))
        with CaptureQueriesContext(connection) as consultas:
            desvios.evaluar_estudio(estudio, asignaciones)
        return len(consultas.captured_queries)

    assert contar(pocos, 300310) == contar(muchos, 300311)


# --- Regla configurable (US 5) ---------------------------------------------------------------


@pytest.mark.django_db
def test_regla_configurable(origen, historia_cloruro, estudio_en_origen, settings):
    actual = estudio_en_origen(origen, dia(3), 300310, {"CL-": "16"}, validar_todo=False)
    settings.AQUALAB_DESVIOS = {"umbral": "50", "cantidad": 3}
    assert evaluacion_de(actual) is None
    settings.AQUALAB_DESVIOS = {"umbral": "30", "cantidad": 2}
    deteccion = evaluacion_de(actual)
    assert deteccion.referencia == Decimal(115) and deteccion.cantidad == 2
    assert desvios.regla() == Regla(Decimal("30"), 2)


@pytest.mark.parametrize(
    "configuracion",
    [
        {"umbral": "0", "cantidad": 3},
        {"umbral": "-5", "cantidad": 3},
        {"umbral": "30", "cantidad": 0},
        {"umbral": "treinta", "cantidad": 3},
        {"cantidad": 3},
        {},
    ],
)
def test_regla_invalida(settings, configuracion):
    from django.core.exceptions import ImproperlyConfigured

    settings.AQUALAB_DESVIOS = configuracion
    with pytest.raises(ImproperlyConfigured):
        desvios.regla()


def test_regla_en_un_solo_lugar():
    """Solo `estudios/desvios.py` lee la configuración de la regla (FR-003)."""
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[2]
    lectores = sorted(
        str(ruta.relative_to(raiz))
        for app in ("estudios", "informes")
        for ruta in (raiz / app).rglob("*.py")
        if "tests" not in ruta.parts
        and "migrations" not in ruta.parts
        and "AQUALAB_DESVIOS" in ruta.read_text(encoding="utf-8")
    )
    assert lectores == ["estudios/desvios.py"]
