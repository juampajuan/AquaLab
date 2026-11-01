import csv
from decimal import Decimal
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError

from pruebas.formulas import CalculoImposible, FormulaInvalida, evaluar_formula, validar_formula
from pruebas.models import Prueba

CATALOGO = Path(__file__).resolve().parent.parent / "datos" / "catalogo_pruebas_agua.csv"


def d(texto):
    return Decimal(texto)


# Un caso conocido por cada fórmula distinta del catálogo, con el valor exacto calculado aparte
# con Decimal (precisión 34).
CASOS = [
    ("x*10", d("2.35"), {}, d("23.5")),
    ("x*20", d("12.5"), {}, d("250")),
    ("x*0.28*5", d("1.2"), {}, d("1.68")),
    ("(25*0.05-x*0.05)*0.01408*100/50*10000", d("10"), {}, d("211.2")),
    ("((x*321.41/140)*10/5*0.51)", d("0.5"), {}, d("1.170850714285714285714285714285714")),
    ("(x*39.1/5)", d("0.4"), {}, d("3.128")),
    ("{COND}*0.54", None, {"COND": d("500")}, d("270")),
    ("({NTK-T}-{NH4})", None, {"NTK-T": d("211.2"), "NH4": d("1.68")}, d("209.52")),
    ("({DUREZA-T}-{CA}*2.5)*0.243", None, {"DUREZA-T": d("300"), "CA": d("80")}, d("24.3")),
    (
        "{NA}/sqrt(({CA}+{MG})/2)",
        None,
        {"NA": d("46"), "CA": d("80"), "MG": d("24.3")},
        d("6.369871557771944953837612155742279"),
    ),
    (
        "({NA-MEQ}+{K-MEQ}+{CA-MEQ}+{MG-MEQ})",
        None,
        {
            "NA-MEQ": d("2"),
            "K-MEQ": d("0.08"),
            "CA-MEQ": d("4"),
            "MG-MEQ": d("1.991803278688524590163934426229508"),
        },
        d("8.071803278688524590163934426229508"),
    ),
    ("{ALC-BO3}*1.22", None, {"ALC-BO3": d("150")}, d("183")),
    ("{ALC-CO3}*0.6", None, {"ALC-CO3": d("20")}, d("12")),
    ("{CO3}/30", None, {"CO3": d("0.12")}, d("0.004")),
    ("{HCO3}/61", None, {"HCO3": d("183")}, d("3")),
    ("{NA}/23", None, {"NA": d("46")}, d("2")),
    ("{K}/39.1", None, {"K": d("3.128")}, d("0.08")),
    ("{CA}/20", None, {"CA": d("80")}, d("4")),
    ("{MG}/12.2", None, {"MG": d("24.3")}, d("1.991803278688524590163934426229508")),
    ("{CL-}/35.5", None, {"CL-": d("71")}, d("2")),
    (
        "{COND}/{CATIONES}",
        None,
        {"COND": d("500"), "CATIONES": d("6.5")},
        d("76.92307692307692307692307692307692"),
    ),
]


@pytest.mark.parametrize("formula,x,resultados,esperado", CASOS)
def test_evaluar_formula_casos_conocidos(formula, x, resultados, esperado):
    assert evaluar_formula(formula, x, resultados) == esperado


@pytest.mark.parametrize(
    "formula,x,resultados,esperado",
    [
        ("-x+3", d("1"), {}, d("2")),
        ("+x", d("1.5"), {}, d("1.5")),
        ("2*(3+4)", None, {}, d("14")),
        ("10/4", None, {}, d("2.5")),
        ("2-3-4", None, {}, d("-5")),
        ("16/4/2", None, {}, d("2")),
        ("sqrt(16)", None, {}, d("4")),
        ("{ A } * 2", None, {"A": d("3")}, d("6")),
    ],
)
def test_evaluar_formula_operadores(formula, x, resultados, esperado):
    assert evaluar_formula(formula, x, resultados) == esperado


def test_formulas_cubren_el_catalogo():
    with CATALOGO.open(encoding="utf-8") as archivo:
        formulas = {fila["formula"] for fila in csv.DictReader(archivo) if fila["formula"]}
    assert formulas <= {formula for formula, *_ in CASOS}


def test_evaluar_formula_division_por_cero():
    with pytest.raises(CalculoImposible) as error:
        evaluar_formula("{COND}/{CATIONES}", None, {"COND": d("500"), "CATIONES": d("0")})
    assert error.value.motivo == "división por cero"


def test_evaluar_formula_raiz_negativa():
    with pytest.raises(CalculoImposible) as error:
        evaluar_formula("sqrt(x)", d("-1"), {})
    assert error.value.motivo == "raíz cuadrada de un número negativo"


def test_evaluar_formula_sin_x():
    with pytest.raises(CalculoImposible) as error:
        evaluar_formula("x*10", None, {})
    assert error.value.motivo == "la fórmula usa el valor medido y la prueba no tiene medición"


@pytest.mark.parametrize(
    "formula",
    [
        "",
        "__import__('os')",
        "x**2",
        "1e3",
        "abs(x)",
        "{}",
        "(x+1",
        "x+",
        "x y",
        "1,5*x",
        "y*2",
        "sqrt x",
        "x+1)",
    ],
)
def test_validar_formula_rechaza(formula):
    with pytest.raises(FormulaInvalida):
        validar_formula(formula)
    with pytest.raises(FormulaInvalida):
        evaluar_formula(formula, d("1"), {})


def test_formulas_del_catalogo_validas():
    with CATALOGO.open(encoding="utf-8") as archivo:
        formulas = [fila["formula"] for fila in csv.DictReader(archivo) if fila["formula"]]
    assert len(formulas) == 25
    for formula in formulas:
        validar_formula(formula)


@pytest.mark.django_db
def test_prueba_clean_rechaza_formula_invalida():
    prueba = Prueba(codigo="T", nombre="T", tipo_calculo="FORMULA", formula="x**2")
    with pytest.raises(ValidationError) as error:
        prueba.full_clean()
    assert "formula" in error.value.message_dict
