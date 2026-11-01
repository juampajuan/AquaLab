import io
from decimal import Decimal

import pytest
from django.core.management import call_command

from pruebas.limites import (
    AUSENTE,
    NO_COMPARABLE,
    Evaluacion,
    LimitesAplicables,
    evaluar,
    leer_limite,
    limites_aplicables,
)
from pruebas.models import Prueba


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("8.5", Decimal("8.5")),
        ("7,01", Decimal("7.01")),
        ("350.0", Decimal("350.0")),
        ("2000", Decimal("2000")),
        ("", None),
        ("  ", None),
        ("Ausente", AUSENTE),
        ("ausencia", AUSENTE),
        (" AUSENTE ", AUSENTE),
        ("SOE", NO_COMPARABLE),
        ("NE", NO_COMPARABLE),
        ("Ph-0,2", NO_COMPARABLE),
        ("Ph+0,2", NO_COMPARABLE),
    ],
)
def test_leer_limite(texto, esperado):
    assert leer_limite(texto) == esperado


def limites(minimo="", maximo=""):
    return LimitesAplicables(minimo=minimo, maximo=maximo, norma="", origen="general")


@pytest.mark.parametrize(
    ("minimo", "maximo", "valor", "esperada"),
    [
        # pH general: 6.4 a 8.5, bordes inclusivos.
        ("6.4", "8.5", "7.4", Evaluacion.CUMPLE),
        ("6.4", "8.5", "6.4", Evaluacion.CUMPLE),
        ("6.4", "8.5", "8.5", Evaluacion.CUMPLE),
        ("6.4", "8.5", "6.39", Evaluacion.FUERA_DE_NORMA),
        ("6.4", "8.5", "8.51", Evaluacion.FUERA_DE_NORMA),
        # Cloruro: máximo 350.0; se compara el valor completo, no el que se ve redondeado.
        ("", "350.0", "350", Evaluacion.CUMPLE),
        ("", "350.0", "400", Evaluacion.FUERA_DE_NORMA),
        ("", "350.0", "350.00004", Evaluacion.FUERA_DE_NORMA),
        # Solo mínimo.
        ("0.1", "", "0.05", Evaluacion.FUERA_DE_NORMA),
        ("0.1", "", "0.1", Evaluacion.CUMPLE),
        # «Ausente» (E. coli A/P y Sólidos sedimentables) y «Ausencia» (Coliformes fecales).
        ("", "Ausente", "0", Evaluacion.CUMPLE),
        ("", "Ausente", "0.000", Evaluacion.CUMPLE),
        ("", "Ausente", "1", Evaluacion.FUERA_DE_NORMA),
        ("", "Ausente", "0.1", Evaluacion.FUERA_DE_NORMA),
        ("", "Ausencia", "0", Evaluacion.CUMPLE),
        ("", "Ausencia", "3", Evaluacion.FUERA_DE_NORMA),
        # Límites no comparables o inexistentes.
        ("", "SOE", "2", Evaluacion.SIN_LIMITE),
        ("", "NE", "0.3", Evaluacion.SIN_LIMITE),
        ("Ph-0,2", "Ph+0,2", "7.1", Evaluacion.SIN_LIMITE),
        ("", "", "5", Evaluacion.SIN_LIMITE),
    ],
)
def test_evaluar(minimo, maximo, valor, esperada):
    assert evaluar(Decimal(valor), limites(minimo, maximo)) == esperada


@pytest.fixture
def catalogo(db):
    call_command("importar_catalogo_pruebas", stdout=io.StringIO())


@pytest.mark.parametrize(
    ("codigo", "vertido", "minimo", "maximo", "origen"),
    [
        ("PH", "agua", "6.4", "8.5", "general"),
        ("PH", "cloacal", "7.01", "10.0", "cloacal"),
        ("PH", "canal", "6.5", "10", "canal"),
        # La fila del vertido reemplaza a los generales completos (el general es «Ausencia»).
        ("COL-FEC", "canal", "", "2000", "canal"),
        ("COL-FEC", "agua", "", "Ausencia", "general"),
        # Sin fila para ese vertido: generales.
        ("CL-", "cloacal", "", "350.0", "general"),
        ("CL2-LIB", "cloacal", "", "NE", "cloacal"),
    ],
)
def test_limites_aplicables(catalogo, codigo, vertido, minimo, maximo, origen):
    prueba = Prueba.objects.prefetch_related("limites_vertido").get(codigo=codigo)
    aplicables = limites_aplicables(prueba, vertido)
    assert (aplicables.minimo, aplicables.maximo, aplicables.origen) == (minimo, maximo, origen)


def test_limites_aplicables_copia_la_norma_de_la_fila_usada(catalogo):
    prueba = Prueba.objects.get(codigo="PH")
    assert limites_aplicables(prueba, "cloacal").norma == "(AGOSBA) 389/98"
    assert limites_aplicables(prueba, "agua").norma == prueba.norma
