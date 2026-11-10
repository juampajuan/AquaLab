"""Tests de los cálculos de la sección «Calidad» del dashboard (US 8.4): `informes/calidad.py`."""

import ast
import datetime as dt
import re
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from django.conf import settings
from django.utils import timezone

from informes import calidad, tablero
from muestras.models import Origen
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db

ZONA = ZoneInfo("America/Argentina/Buenos_Aires")


def este_mes():
    return tablero.periodo("este_mes", timezone.localdate())


def periodo_a_mano(inicio, fin, inicio_anterior, fin_anterior):
    return tablero.Periodo("este_mes", "Este mes", inicio, fin, inicio_anterior, fin_anterior)


def a_las(fecha, hora, minuto=0):
    return dt.datetime.combine(fecha, dt.time(hora, minuto), tzinfo=ZONA)


# --- Base: porcentaje y conteo -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("parte", "total", "esperado"),
    [
        (4, 40, Decimal("10.0")),
        (1, 3, Decimal("33.3")),
        (2, 3, Decimal("66.7")),
        (1, 8, Decimal("12.5")),
        (1, 16, Decimal("6.3")),  # 6,25: la mitad redondea hacia arriba
        (0, 5, Decimal("0.0")),
        (0, 0, None),
    ],
)
def test_porcentaje(parte, total, esperado):
    resultado = calidad.porcentaje(parte, total)
    assert resultado == esperado
    if esperado is not None:
        assert str(resultado) == str(esperado)  # siempre con un decimal


def test_conteo_texto():
    assert calidad.Conteo(2, 10).texto == "20,0 % (2 de 10)"
    assert calidad.Conteo(0, 0).texto == "Sin resultados"
    assert calidad.Conteo(0, 0).porcentaje is None


# --- US1: nivel de cumplimiento del período ----------------------------------------------------


def test_indicador_general(evaluadas):
    evaluadas({"PH": (0, 10), "TURBIDEZ": (0, 10), "COLOR": (0, 10), "CL-": (4, 10)})
    evaluadas({}, sin_limite={"COND": 3})

    indicador = calidad.indicador(este_mes())

    assert indicador.actual.porcentaje == Decimal("10.0")
    assert indicador.actual.fuera == 4
    assert indicador.actual.evaluados == 40
    assert indicador.sin_limite == 3
    assert indicador.anterior.evaluados == 0
    assert indicador.variacion is None


def test_cuenta_solo_validaciones_vigentes(estudio_en_origen, cliente_a, bioquimico):
    from estudios.servicios import corregir_mediciones
    from estudios.tests.utiles import asignacion_de, validar
    from informes.servicios import emitir_informe

    origen = Origen.objects.create(cliente=cliente_a, nombre="Pozo vigentes")
    hoy = timezone.localdate()
    # Corregida y revalidada: la validación fuera de norma queda anulada; cuenta la nueva (cumple).
    revalidada = estudio_en_origen(origen, hoy, 300701, {"CL-": "40"}, usuario=bioquimico)
    cl = asignacion_de(revalidada, "CL-")
    corregir_mediciones(revalidada.pk, {cl.pk: (Decimal("40"), Decimal("30"))}, bioquimico)
    validar(revalidada, bioquimico, "CL-")
    # Con informe emitido: cuenta.
    emitido = estudio_en_origen(origen, hoy, 300702, {"CL-": "40"}, usuario=bioquimico)
    emitir_informe(emitido.pk, bioquimico)
    # Corregida sin revalidar: la validación queda anulada y no cuenta.
    anulada = estudio_en_origen(origen, hoy, 300703, {"CL-": "40"}, usuario=bioquimico)
    cl = asignacion_de(anulada, "CL-")
    corregir_mediciones(anulada.pk, {cl.pk: (Decimal("40"), Decimal("45"))}, bioquimico)

    actual = calidad.indicador(este_mes()).actual

    assert (actual.fuera, actual.evaluados) == (1, 2)


def test_no_reevalua_con_limites_actuales(estudio_en_origen, cliente_a):
    origen = Origen.objects.create(cliente=cliente_a, nombre="Pozo límites")
    estudio_en_origen(origen, timezone.localdate(), 300711, {"CL-": "40"})  # 400 > 350
    Prueba.objects.filter(codigo="CL-").update(limite_max="500")

    actual = calidad.indicador(este_mes()).actual

    assert (actual.fuera, actual.evaluados) == (1, 1)
    # La única cosa que usa de pruebas/limites.py son los valores de `Evaluacion`: nunca evalúa.
    arbol = ast.parse(Path(calidad.__file__).read_text(encoding="utf-8"))
    desde_limites = {
        alias.name
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.ImportFrom) and nodo.module == "pruebas.limites"
        for alias in nodo.names
    }
    assert desde_limites <= {"Evaluacion"}
    importa_modulo = any(
        isinstance(nodo, ast.Import) and any(a.name == "pruebas.limites" for a in nodo.names)
        for nodo in ast.walk(arbol)
    )
    assert not importa_modulo


def test_usa_el_periodo_del_dashboard(evaluadas):
    hoy = timezone.localdate()
    p = periodo_a_mano(
        hoy - dt.timedelta(days=10),
        hoy - dt.timedelta(days=1),
        hoy - dt.timedelta(days=20),
        hoy - dt.timedelta(days=11),
    )
    evaluadas({"CL-": (1, 1)})  # hoy: fuera del período
    evaluadas({"PH": (0, 2)}, momento=a_las(hoy - dt.timedelta(days=5), 12))
    evaluadas({"COLOR": (1, 3)}, momento=a_las(hoy - dt.timedelta(days=15), 12))

    indicador = calidad.indicador(p)

    assert (indicador.actual.fuera, indicador.actual.evaluados) == (0, 2)
    assert (indicador.anterior.fuera, indicador.anterior.evaluados) == (1, 3)


def test_zona_horaria(evaluadas):
    fin = timezone.localdate() - dt.timedelta(days=3)
    p = periodo_a_mano(
        fin - dt.timedelta(days=6),
        fin,
        fin - dt.timedelta(days=13),
        fin - dt.timedelta(days=7),
    )
    # 23:30 en Buenos Aires ya es el día siguiente en UTC: igual cuenta en el período.
    evaluadas({"CL-": (1, 1)}, momento=a_las(fin, 23, 30))
    evaluadas({"PH": (1, 1)}, momento=a_las(fin + dt.timedelta(days=1), 0, 30))

    actual = calidad.indicador(p).actual

    assert settings.TIME_ZONE == "America/Argentina/Buenos_Aires"
    assert (actual.fuera, actual.evaluados) == (1, 1)


@pytest.mark.parametrize(
    ("actual", "anterior", "texto", "tono"),
    [
        ((4, 40), (1, 20), "▲ +5,0 p. p.", "peligro"),
        ((1, 20), (4, 40), "▼ −5,0 p. p.", "exito"),
        ((1, 10), (2, 20), "= 0,0 p. p.", "neutro"),
        ((4, 40), (0, 0), None, None),
        ((0, 0), (4, 40), None, None),
    ],
)
def test_variacion_del_porcentaje(actual, anterior, texto, tono):
    variacion = calidad.variacion_calidad(calidad.Conteo(*actual), calidad.Conteo(*anterior))
    if texto is None:
        assert variacion is None
    else:
        assert (variacion.texto, variacion.tono) == (texto, tono)


def test_variacion_en_el_indicador(evaluadas):
    hoy = timezone.localdate()
    p = periodo_a_mano(
        hoy - dt.timedelta(days=10),
        hoy,
        hoy - dt.timedelta(days=21),
        hoy - dt.timedelta(days=11),
    )
    evaluadas({"CL-": (4, 40)})
    evaluadas({"CL-": (1, 20)}, momento=a_las(hoy - dt.timedelta(days=15), 12))

    variacion = calidad.indicador(p).variacion

    assert (variacion.texto, variacion.tono) == ("▲ +5,0 p. p.", "peligro")


# --- US2: pruebas que más fallan ---------------------------------------------------------------

DOCE = (
    "AG",
    "AL",
    "BO",
    "CA",
    "CADMIO",
    "CL-",
    "COBRE",
    "COLOR",
    "COND",
    "IAC",
    "PH",
    "TURBIDEZ",
)


@pytest.mark.parametrize(
    ("por_codigo", "esperado", "restantes"),
    [
        pytest.param(
            {"CL-": (2, 10), "ECOLI": (2, 8), "PH": (3, 4)},
            [("ECOLI", "25,0 % (2 de 8)"), ("CL-", "20,0 % (2 de 10)")],
            0,
            id="orden-y-minimo",
        ),
        pytest.param(
            {"PH": (3, 5), "CL-": (0, 10)},
            [("PH", "60,0 % (3 de 5)")],
            0,
            id="cinco-entra-sin-fuera-no",
        ),
        pytest.param(
            {"PH": (1, 5), "TURBIDEZ": (2, 10), "COLOR": (1, 5)},
            [
                ("TURBIDEZ", "20,0 % (2 de 10)"),
                ("COLOR", "20,0 % (1 de 5)"),
                ("PH", "20,0 % (1 de 5)"),
            ],
            0,
            id="empate-mas-fuera-y-codigo",
        ),
        pytest.param(
            {"COLOR": (2, 6), "TURBIDEZ": (5, 15)},
            [("TURBIDEZ", "33,3 % (5 de 15)"), ("COLOR", "33,3 % (2 de 6)")],
            0,
            id="misma-fraccion",
        ),
        pytest.param(
            dict.fromkeys(DOCE, (1, 5)),
            [(codigo, "20,0 % (1 de 5)") for codigo in DOCE[:10]],
            2,
            id="tope-de-diez",
        ),
    ],
)
def test_ranking_de_pruebas(evaluadas, por_codigo, esperado, restantes):
    evaluadas(por_codigo)

    lista = calidad.pruebas(este_mes())

    assert [(fila.codigo, fila.conteo.texto) for fila in lista.filas] == esperado
    assert lista.restantes == restantes


def test_ranking_no_cuenta_sin_limite(evaluadas):
    evaluadas({"CL-": (1, 4)}, sin_limite={"CL-": 3})  # 4 evaluados: no llega al mínimo

    assert calidad.pruebas(este_mes()).filas == []


def test_ranking_con_nombre(evaluadas, catalogo):
    evaluadas({"CL-": (1, 5)})

    (fila,) = calidad.pruebas(este_mes()).filas

    assert fila.nombre == catalogo["CL-"].nombre


def test_minimo_definido_en_un_solo_lugar(evaluadas, monkeypatch):
    assert calidad.MINIMO_EVALUADOS_RANKING == 5
    evaluadas({"PH": (2, 3)})
    assert calidad.pruebas(este_mes()).filas == []

    monkeypatch.setattr(calidad, "MINIMO_EVALUADOS_RANKING", 3)

    assert [fila.codigo for fila in calidad.pruebas(este_mes()).filas] == ["PH"]
    assert calidad.armar(este_mes())["minimo_ranking"] == 3

    raiz = Path(settings.BASE_DIR)
    plantilla = raiz / "informes" / "templates" / "informes" / "calidad.html"
    assert "al menos 5" not in plantilla.read_text(encoding="utf-8")
    definicion = re.compile(r"^\s*MINIMO_EVALUADOS_RANKING\s*=", re.M)
    otros = [
        archivo
        for app in ("informes", "estudios")
        for archivo in (raiz / app).rglob("*.py")
        if archivo != Path(calidad.__file__) and definicion.search(archivo.read_text("utf-8"))
    ]
    assert otros == []


def test_armar_datos_del_grafico(evaluadas):
    evaluadas({"CL-": (2, 10), "ECOLI": (2, 8)})

    datos = calidad.armar(este_mes())

    assert datos["graficos"]["calidad_pruebas"] == {
        "etiquetas": ["ECOLI · E. Coli", "CL- · Cloruro"],
        "porcentajes": ["25.0", "20.0"],
    }
