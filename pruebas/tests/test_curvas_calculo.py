"""US 6.6 – recta por mínimos cuadrados (`curvas.ajustar`, research R2)."""

from decimal import Decimal

import pytest

from pruebas import curvas

D = Decimal

# Caso de referencia de research.md R2 (calculado aparte con Decimal, precisión 40).
REFERENCIA = [
    ("0", "0.000"),
    ("0.1", "0.052"),
    ("0.2", "0.101"),
    ("0.3", "0.153"),
    ("0.4", "0.199"),
]


def puntos(pares):
    return [(D(c), D(a)) for c, a in pares]


def test_ajustar_caso_referencia():
    ajuste = curvas.ajustar(puntos(REFERENCIA))
    assert ajuste.pendiente == D("0.499000000000")
    assert ajuste.ordenada == D("0.001200000000")
    assert ajuste.r2 == D("0.9996025692")
    assert (ajuste.concentracion_min, ajuste.concentracion_max) == (D("0"), D("0.4"))
    assert (ajuste.absorbancia_min, ajuste.absorbancia_max) == (D("0"), D("0.199"))
    assert ajuste.r2_bajo is False
    # Con los valores guardados, como el cálculo del resultado.
    concentracion = (D("0.126") - ajuste.ordenada) / ajuste.pendiente
    assert concentracion.quantize(D("1E-10")) == D("0.2501002004")


def test_ajustar_redondeo_de_lo_guardado():
    ajuste = curvas.ajustar(puntos(REFERENCIA))
    assert ajuste.pendiente.as_tuple().exponent == -12
    assert ajuste.ordenada.as_tuple().exponent == -12
    assert ajuste.r2.as_tuple().exponent == -10


def test_ajustar_replicas():
    """Las réplicas de un estándar entran todas; el blanco no fuerza la recta al origen."""
    ajuste = curvas.ajustar(
        puntos([("0", "0.010"), ("0", "0.012"), ("1", "0.511"), ("1", "0.509"), ("2", "1.010")])
    )
    # Valores calculados aparte con Decimal (precisión 40), como el caso de referencia.
    assert ajuste.pendiente == D("0.499428571429")
    assert ajuste.ordenada == D("0.010857142857")
    assert ajuste.r2 == D("0.9999938636")


@pytest.mark.parametrize(
    "pares, mensaje",
    [
        ([("0", "0"), ("1", "0.5")], curvas.MENSAJE_POCOS_PUNTOS),
        ([("1", "0.1"), ("1", "0.2"), ("1", "0.3")], curvas.MENSAJE_CONCENTRACIONES_IGUALES),
        ([("0", "0.2"), ("1", "0.2"), ("2", "0.2")], curvas.MENSAJE_ABSORBANCIAS_IGUALES),
        (
            [("0", "0"), ("400000000000", "0.000001"), ("800000000000", "0.000002")],
            curvas.MENSAJE_PENDIENTE_CERO,
        ),
        ([("0", "0"), ("-1", "0.5"), ("2", "1")], curvas.MENSAJE_NEGATIVO),
        ([("0", "0"), ("1", "-0.5"), ("2", "1")], curvas.MENSAJE_NEGATIVO),
    ],
    ids=[
        "dos puntos",
        "concentraciones iguales",
        "absorbancias iguales",
        "pendiente 0",
        "conc<0",
        "abs<0",
    ],
)
def test_ajustar_rechaza(pares, mensaje):
    with pytest.raises(curvas.CurvaInvalida) as error:
        curvas.ajustar(puntos(pares))
    assert mensaje in error.value.errores.values()


def test_r2_bajo():
    ajuste = curvas.ajustar(puntos([("0", "0"), ("1", "0.5"), ("2", "0.7"), ("3", "1.6")]))
    assert ajuste.r2 == D("0.9328358209")
    assert ajuste.r2_bajo is True


@pytest.mark.django_db
@pytest.mark.parametrize("r2, bajo", [("0.9949999999", True), ("0.995", False), ("1", False)])
def test_r2_bajo_en_el_borde(prueba_curva, curva_de, r2, bajo):
    assert curva_de(prueba_curva, r2=r2).r2_bajo is bajo


@pytest.mark.django_db
def test_concentracion(prueba_curva, curva_de):
    curva = curva_de(prueba_curva)  # pendiente 0,5 · ordenada 0,001
    assert curva.concentracion(D("0.126")) == D("0.25")
