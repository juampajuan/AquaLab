"""Cálculo del historial de un origen y de su variación (US 8.1): `estudios/comparacion.py`."""

import datetime as dt
from decimal import Decimal

import pytest

from estudios import comparacion
from estudios.comparacion import Punto
from estudios.models import EstadoPruebaEstudio, PruebaEstudio, Resultado, Validacion
from estudios.servicios import corregir_mediciones
from estudios.tests.conftest import en_grupo_bioquimicos
from estudios.tests.utiles import asignacion_de
from muestras.models import Origen
from pruebas.limites import Evaluacion

pytestmark = pytest.mark.django_db

DIA = dt.date(2026, 1, 10)


def dia(n):
    return DIA + dt.timedelta(days=n)


@pytest.fixture
def origen(cliente_a):
    return Origen.objects.create(cliente=cliente_a, nombre="Pozo de comparación")


@pytest.fixture
def otro_origen(cliente_a):
    return Origen.objects.create(cliente=cliente_a, nombre="Otro pozo")


def historial_de(historiales, codigo):
    (encontrado,) = [h for h in historiales if h.prueba.codigo == codigo]
    return encontrado


def valores(historial):
    return [p.valor for p in historial.puntos]


# --- Historial (FR-003, FR-004, FR-020) ------------------------------------------------------


def test_historial_solo_validados(origen, otro_origen, estudio_en_origen, empleado):
    estudio_en_origen(origen, dia(0), 300001, {"CL-": "10"})
    estudio_en_origen(origen, dia(1), 300002, {"CL-": "11"}, validar_todo=False)
    anulado = estudio_en_origen(origen, dia(2), 300003, {"CL-": "12"})
    estudio_en_origen(otro_origen, dia(3), 300004, {"CL-": "13"})
    estudio_en_origen(origen, dia(4), 300005, {"PH": "7.0"})
    # Corregir después de validar anula la validación (US 6.3): deja de ser historial.
    asignacion = asignacion_de(anulado, "CL-")
    corregir_mediciones(anulado.pk, {asignacion.pk: (Decimal("12"), Decimal("12.5"))}, empleado)
    assert Validacion.objects.filter(asignacion=asignacion, anulada=True).exists()

    historial = historial_de(comparacion.comparar(origen, codigos=["CL-"]), "CL-")

    assert valores(historial) == [Decimal("100")]
    assert all(p.validado for p in historial.puntos)
    assert historial.referencia is None


def test_orden_por_fecha_de_muestreo_y_numero_pi(origen, estudio_en_origen):
    estudio_en_origen(origen, dia(5), 300001, {"CL-": "13"})
    estudio_en_origen(origen, dia(1), 300004, {"CL-": "12"})
    estudio_en_origen(origen, dia(1), 300002, {"CL-": "11"})
    estudio_en_origen(origen, dia(0), 300003, {"CL-": "10"})

    historial = historial_de(comparacion.comparar(origen), "CL-")

    assert [p.numero_pi for p in historial.puntos] == [300003, 300002, 300004, 300001]
    assert valores(historial) == [Decimal("100"), Decimal("110"), Decimal("120"), Decimal("130")]


def test_varios_estudios_de_una_muestra(origen, estudio_en_origen, catalogo, empleado):
    from estudios.models import TipoEstudio
    from estudios.servicios import crear_estudio
    from estudios.tests.utiles import cargar, validar

    primero = estudio_en_origen(origen, dia(0), 300001, {"CL-": "10"})
    tipo = TipoEstudio.objects.create(nombre="Otro tipo con cloruro")
    tipo.pruebas.set([catalogo["CL-"]])
    segundo = crear_estudio(
        {
            "clave": "1d0e9a8e-1111-4f00-9000-000000000001",
            "muestra": primero.muestra.pk,
            "tipo": tipo.pk,
            "version": tipo.version,
        },
        empleado,
    )
    cargar(segundo, empleado, {"CL-": "11"})
    validar(segundo, en_grupo_bioquimicos(empleado), "CL-")

    historial = historial_de(comparacion.comparar(origen), "CL-")

    assert [(p.numero_pi, p.estudio_pk) for p in historial.puntos] == [
        (300001, primero.pk),
        (300001, segundo.pk),
    ]


def test_otra_unidad_fuera_del_grafico(origen, estudio_en_origen):
    viejo = estudio_en_origen(origen, dia(0), 300001, {"CL-": "10"})
    estudio_en_origen(origen, dia(1), 300002, {"CL-": "12"})
    actual = estudio_en_origen(origen, dia(2), 300003, {"CL-": "14"}, validar_todo=False)
    Resultado.objects.filter(asignacion__estudio=viejo).update(unidad="g/l")

    historial = historial_de(comparacion.comparar(origen, estudio=actual), "CL-")

    distinto = [p for p in historial.puntos if p.otra_unidad]
    assert [p.numero_pi for p in distinto] == [300001]
    assert distinto[0].unidad == "g/l"
    assert historial.unidad == "mg/l"
    assert historial.variacion.cantidad_anteriores == 1
    assert historial.variacion.promedio == Decimal("120")


def test_otra_unidad_sola_no_es_historial(origen, estudio_en_origen):
    viejo = estudio_en_origen(origen, dia(0), 300001, {"CL-": "10"})
    actual = estudio_en_origen(origen, dia(1), 300002, {"CL-": "14"}, validar_todo=False)
    Resultado.objects.filter(asignacion__estudio=viejo).update(unidad="g/l")

    historial = historial_de(comparacion.comparar(origen, estudio=actual), "CL-")

    assert not historial.tiene_historial
    assert historial.variacion is None


def test_estudio_de_otro_origen_es_error(origen, otro_origen, estudio_en_origen):
    ajeno = estudio_en_origen(otro_origen, dia(0), 300001, {"CL-": "10"})

    with pytest.raises(ValueError):
        comparacion.comparar(origen, estudio=ajeno)


def test_pruebas_disponibles(origen, estudio_en_origen):
    estudio_en_origen(origen, dia(0), 300001, {"PH": "7.0", "CL-": "10"})
    estudio_en_origen(origen, dia(1), 300002, {"COND": "500"}, validar_todo=False)
    actual = estudio_en_origen(origen, dia(2), 300003, {"TURBIDEZ": "1", "CL-": "10"})

    sin_estudio = comparacion.pruebas_disponibles(origen)
    con_estudio = comparacion.pruebas_disponibles(origen, actual)

    # Sin estudio: las que tienen algún validado, por nombre (Cloruro, pH, Turbidez).
    assert [p.codigo for p in sin_estudio] == ["CL-", "PH", "TURBIDEZ"]
    # Con estudio: las del estudio, por código.
    assert [p.codigo for p in con_estudio] == ["CL-", "TURBIDEZ"]


def test_comparar_con_estudio_usa_sus_pruebas(origen, estudio_en_origen):
    estudio_en_origen(origen, dia(0), 300001, {"PH": "7.0", "CL-": "10"})
    actual = estudio_en_origen(origen, dia(1), 300002, {"CL-": "12"}, validar_todo=False)

    historiales = comparacion.comparar(origen, estudio=actual)

    assert [h.prueba.codigo for h in historiales] == ["CL-"]


def test_codigos_filtra(origen, estudio_en_origen):
    estudio_en_origen(origen, dia(0), 300001, {"PH": "7.0", "CL-": "10"})

    historiales = comparacion.comparar(origen, codigos=["PH"])

    assert [h.prueba.codigo for h in historiales] == ["PH"]


# --- Referencia (FR-005, FR-007) -------------------------------------------------------------


def test_referencia_destacada_sin_validar(origen, estudio_en_origen):
    estudio_en_origen(origen, dia(0), 300001, {"CL-": "10"})
    actual = estudio_en_origen(origen, dia(1), 300002, {"CL-": "40"}, validar_todo=False)

    historial = historial_de(comparacion.comparar(origen, estudio=actual), "CL-")

    assert historial.referencia.es_referencia
    assert not historial.referencia.validado
    assert historial.referencia.valor == Decimal("400")
    assert historial.referencia.evaluacion == Evaluacion.FUERA_DE_NORMA
    assert historial.puntos[-1] is historial.referencia
    assert historial.fuera_de_franja
    assert not historial.sin_resultado


def test_referencia_validada(origen, estudio_en_origen):
    estudio_en_origen(origen, dia(0), 300001, {"CL-": "10"})
    actual = estudio_en_origen(origen, dia(1), 300002, {"CL-": "12"})

    historial = historial_de(comparacion.comparar(origen, estudio=actual), "CL-")

    assert historial.referencia.validado
    assert historial.referencia.evaluacion == Evaluacion.CUMPLE
    # El estudio de referencia no se repite como punto del historial.
    assert [p.estudio_pk for p in historial.puntos].count(actual.pk) == 1


def test_referencia_sin_resultado(origen, estudio_en_origen):
    estudio_en_origen(origen, dia(0), 300001, {"CL-": "10"})
    actual = estudio_en_origen(origen, dia(1), 300002, {"CL-": None})

    historial = historial_de(comparacion.comparar(origen, estudio=actual), "CL-")

    assert historial.sin_resultado
    assert historial.referencia is None
    assert historial.tiene_historial
    assert valores(historial) == [Decimal("100")]
    assert historial.variacion is None


def test_prueba_sin_historial(origen, estudio_en_origen):
    actual = estudio_en_origen(origen, dia(0), 300001, {"CL-": "12"}, validar_todo=False)

    historial = historial_de(comparacion.comparar(origen, estudio=actual), "CL-")

    assert not historial.tiene_historial
    assert historial.referencia.texto == "120"
    assert historial.variacion is None


def test_texto_de_punto_bajo_deteccion_y_presencia(origen, estudio_en_origen):
    estudio_en_origen(origen, dia(0), 300001, {"CL-": "0.001", "ECOLI": "1"})

    historiales = comparacion.comparar(origen)

    assert historial_de(historiales, "CL-").puntos[0].texto == "< 0,1"
    assert historial_de(historiales, "ECOLI").puntos[0].texto == "Presente"
    assert historial_de(historiales, "ECOLI").presencia


# --- Franja (FR-006) -------------------------------------------------------------------------


def test_franja_solo_maximo(catalogo):
    franja = comparacion.franja(catalogo["CL-"], "agua")

    assert franja.comparable
    assert (franja.minimo, franja.maximo) == (None, Decimal("350"))
    assert franja.texto == "Máximo 350 mg/l · Límite general"


def test_franja_minimo_y_maximo(catalogo):
    franja = comparacion.franja(catalogo["PH"], "agua")

    assert (franja.minimo, franja.maximo) == (Decimal("6.4"), Decimal("8.5"))
    assert franja.texto == "Entre 6,4 y 8,5 UpH · Límite general"


def test_franja_solo_minimo(catalogo):
    prueba = catalogo["COND"]
    prueba.limite_min = "100"

    franja = comparacion.franja(prueba, "agua")

    assert (franja.minimo, franja.maximo) == (Decimal("100"), None)
    assert franja.texto == "Mínimo 100 microsiemens/cm2 · Límite general"


def test_franja_ausente(catalogo):
    franja = comparacion.franja(catalogo["ECOLI"], "agua")

    assert franja.comparable and franja.presencia
    assert franja.texto == "Ausente · Límite general"


@pytest.mark.parametrize("codigo", ["PH-SAT", "COND"])
def test_franja_no_comparable_o_sin_limite(catalogo, codigo):
    franja = comparacion.franja(catalogo[codigo], "agua")

    assert not franja.comparable
    assert franja.texto == "Sin límite comparable"


def test_franja_por_vertido(catalogo):
    franja = comparacion.franja(catalogo["COL-FEC"], "cloacal")

    assert franja.maximo == Decimal("20000")
    assert franja.texto.endswith("· Vertido cloacal")


def test_franja_usa_el_vertido_de_la_referencia(origen, estudio_en_origen):
    estudio_en_origen(origen, dia(0), 300001, {"COL-FEC": "5"})
    actual = estudio_en_origen(
        origen, dia(1), 300002, {"COL-FEC": "8"}, validar_todo=False, tipo_vertido="cloacal"
    )

    historial = historial_de(comparacion.comparar(origen, estudio=actual), "COL-FEC")

    assert historial.franja.maximo == Decimal("20000")


# --- Consultas (SC-005) ----------------------------------------------------------------------


def crear_historia(origen, estudio_en_origen, cantidad):
    for n in range(cantidad):
        estudio_en_origen(origen, dia(n), 310000 + n, {"CL-": "10", "PH": "7.0", "TURBIDEZ": "1"})
    return estudio_en_origen(
        origen,
        dia(cantidad),
        320000 + cantidad,
        {"CL-": "12", "PH": "7.1", "TURBIDEZ": "1.2"},
        validar_todo=False,
    )


def contar_consultas(django_assert_max_num_queries, origen, actual):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    from estudios.models import Estudio

    # Como en la vista: el estudio llega con su muestra.
    actual = Estudio.objects.select_related("muestra").get(pk=actual.pk)
    with django_assert_max_num_queries(8), CaptureQueriesContext(connection) as consultas:
        comparacion.comparar(origen, estudio=actual)
    return len(consultas)


def test_consultas_fijas(origen, estudio_en_origen, django_assert_max_num_queries):
    actual = crear_historia(origen, estudio_en_origen, 6)
    con_seis = contar_consultas(django_assert_max_num_queries, origen, actual)

    for n in range(6, 12):
        estudio_en_origen(origen, dia(20 + n), 330000 + n, {"CL-": "10", "PH": "7.0"})
    con_doce = contar_consultas(django_assert_max_num_queries, origen, actual)

    assert con_seis == con_doce


# --- Variación (FR-008 a FR-011) -------------------------------------------------------------


def serie(origen, estudio_en_origen, mediciones, actual=None, codigo="CL-"):
    """Valida las mediciones en días sucesivos y, si hay `actual`, la deja de referencia."""
    for n, medido in enumerate(mediciones):
        estudio_en_origen(origen, dia(n), 300001 + n, {codigo: medido})
    if actual is None:
        return None
    return estudio_en_origen(
        origen, dia(len(mediciones)), 309999, {codigo: actual}, validar_todo=False
    )


def test_variacion_contra_anterior_y_promedio(origen, estudio_en_origen):
    actual = serie(origen, estudio_en_origen, ["10", "12", "14"], actual="21")

    variacion = historial_de(comparacion.comparar(origen, estudio=actual), "CL-").variacion

    assert variacion.ultimo.valor == Decimal("210")
    assert variacion.anterior.valor == Decimal("140")
    assert variacion.cantidad_anteriores == 3
    assert variacion.contra_anterior.diferencia == Decimal("70")
    assert variacion.contra_anterior.porcentaje == Decimal("50.0")
    assert variacion.contra_anterior.flecha == "▲"
    assert variacion.contra_anterior.texto == "+70 mg/l (+50,0 %)"
    assert variacion.promedio == Decimal("120")
    assert variacion.promedio_texto == "120 mg/l"
    assert variacion.contra_promedio.texto == "+90 mg/l (+75,0 %)"


def test_baja_con_flecha_abajo_e_igual(origen, estudio_en_origen):
    actual = serie(origen, estudio_en_origen, ["20", "12"], actual="9")

    variacion = historial_de(comparacion.comparar(origen, estudio=actual), "CL-").variacion

    assert variacion.contra_anterior.flecha == "▼"
    assert variacion.contra_anterior.texto == "-30 mg/l (-25,0 %)"
    assert variacion.contra_promedio.texto == "-70 mg/l (-43,8 %)"

    igual = comparacion.variacion(
        punto(Decimal("5")), [punto(Decimal("5"))], unidad="mg/l"
    ).contra_anterior
    assert (igual.flecha, igual.texto) == ("=", "0 mg/l (0,0 %)")


def test_un_solo_anterior(origen, estudio_en_origen):
    actual = serie(origen, estudio_en_origen, ["10"], actual="15")

    variacion = historial_de(comparacion.comparar(origen, estudio=actual), "CL-").variacion

    assert variacion.contra_anterior.texto == variacion.contra_promedio.texto
    assert variacion.contra_anterior.texto == "+50 mg/l (+50,0 %)"


def test_sin_anteriores_sin_variacion(origen, estudio_en_origen):
    serie(origen, estudio_en_origen, ["10"])

    assert historial_de(comparacion.comparar(origen), "CL-").variacion is None


def test_ultimo_sin_referencia_es_el_mas_reciente(origen, estudio_en_origen):
    serie(origen, estudio_en_origen, ["10", "12", "14"])

    variacion = historial_de(comparacion.comparar(origen), "CL-").variacion

    assert variacion.ultimo.valor == Decimal("140")
    assert variacion.cantidad_anteriores == 2
    assert variacion.promedio == Decimal("110")


def test_anteriores_solo_de_muestras_previas(origen, estudio_en_origen, catalogo, empleado):
    from estudios.models import TipoEstudio
    from estudios.servicios import crear_estudio
    from estudios.tests.utiles import cargar, validar

    estudio_en_origen(origen, dia(0), 300001, {"CL-": "10"})
    referencia = estudio_en_origen(origen, dia(1), 300002, {"CL-": "20"}, validar_todo=False)
    estudio_en_origen(origen, dia(2), 300003, {"CL-": "30"})
    # Otro estudio validado de la misma muestra que la referencia.
    tipo = TipoEstudio.objects.create(nombre="Otro tipo de la misma muestra")
    tipo.pruebas.set([catalogo["CL-"]])
    hermano = crear_estudio(
        {
            "clave": "1d0e9a8e-2222-4f00-9000-000000000002",
            "muestra": referencia.muestra.pk,
            "tipo": tipo.pk,
            "version": tipo.version,
        },
        empleado,
    )
    cargar(hermano, empleado, {"CL-": "25"})
    validar(hermano, en_grupo_bioquimicos(empleado), "CL-")

    historial = historial_de(comparacion.comparar(origen, estudio=referencia), "CL-")

    assert valores(historial) == [Decimal("100"), Decimal("200"), Decimal("250"), Decimal("300")]
    assert historial.variacion.cantidad_anteriores == 1
    assert historial.variacion.anterior.valor == Decimal("100")


def test_base_cero_sin_porcentaje(origen, estudio_en_origen):
    actual = serie(origen, estudio_en_origen, ["0"], actual="0.5")

    variacion = historial_de(comparacion.comparar(origen, estudio=actual), "CL-").variacion

    assert variacion.contra_anterior.porcentaje is None
    assert variacion.contra_anterior.texto == "+5 mg/l (sin porcentaje: valor previo 0)"


def punto(valor, numero_pi=1, unidad="mg/l"):
    return Punto(
        fecha_muestreo=DIA,
        numero_pi=numero_pi,
        muestra_pk=numero_pi,
        estudio_pk=numero_pi,
        valor=valor,
        texto=str(valor),
        unidad=unidad,
        tipo_vertido="agua",
        validado=True,
        evaluacion=Evaluacion.CUMPLE,
    )


def test_decimal_valor_completo():
    anteriores = [punto(Decimal("1.00004")), punto(Decimal("1.00006"))]
    ultimo = punto(Decimal("1.5000149"))

    variacion = comparacion.variacion(ultimo, anteriores, unidad="mg/l")

    # Con los valores redondeados a 4 decimales (1 y 1,0001) el anterior daría otra diferencia.
    assert variacion.contra_anterior.diferencia == Decimal("0.4999549")
    assert variacion.promedio == Decimal("1.00005")
    assert variacion.contra_anterior.porcentaje == Decimal("50.0")
    assert variacion.contra_anterior.texto == "+0,5 mg/l (+50,0 %)"
    # 0,4999649 / 1,00005 ≈ 49,994 %: se redondea al décimo con ROUND_HALF_UP.
    assert variacion.contra_promedio.porcentaje == Decimal("50.0")
    for valor in (
        variacion.promedio,
        variacion.contra_anterior.diferencia,
        variacion.contra_anterior.porcentaje,
        variacion.contra_promedio.diferencia,
    ):
        assert isinstance(valor, Decimal)


def test_porcentaje_redondeo_medio_hacia_arriba():
    variacion = comparacion.variacion(punto(Decimal("100.05")), [punto(Decimal("100"))])

    assert variacion.contra_anterior.porcentaje == Decimal("0.1")  # 0,05 % → 0,1
    assert variacion.contra_anterior.texto == "+0,05 (+0,1 %)"


def test_variacion_presencia():
    ausente, presente = Decimal(0), Decimal(1)

    cambio = comparacion.variacion(
        punto(presente, 3, "A/P"),
        [punto(ausente, 1, "A/P"), punto(ausente, 2, "A/P")],
        presencia=True,
    )
    sin_cambio = comparacion.variacion(
        punto(ausente, 3, "A/P"),
        [punto(presente, 1, "A/P"), punto(ausente, 2, "A/P")],
        presencia=True,
    )

    assert cambio.cambio_presencia == "Cambió: Ausente → Presente"
    assert cambio.presentes == 0
    assert cambio.contra_anterior is None and cambio.contra_promedio is None
    assert cambio.promedio is None
    assert sin_cambio.cambio_presencia == "Sin cambios (Ausente)"
    assert sin_cambio.presentes == 1
    assert sin_cambio.cantidad_anteriores == 2


def test_presencia_en_comparar(origen, estudio_en_origen):
    serie(origen, estudio_en_origen, ["0", "1"], actual="0", codigo="ECOLI")
    actual = PruebaEstudio.objects.get(
        prueba__codigo="ECOLI", estado=EstadoPruebaEstudio.CARGADA
    ).estudio

    historial = historial_de(comparacion.comparar(origen, estudio=actual), "ECOLI")

    assert historial.presencia
    assert [p.texto for p in historial.puntos] == ["Ausente", "Presente", "Ausente"]
    assert historial.variacion.cambio_presencia == "Cambió: Presente → Ausente"
    assert historial.variacion.presentes == 1
