"""Fechas dichas en lenguaje natural (US 10.3, research R4)."""

import datetime

import pytest

from asistente.fechas import leer_fecha

HOY = datetime.date(2026, 11, 17)


@pytest.mark.parametrize(
    "texto, esperada",
    [
        ("hoy", datetime.date(2026, 11, 17)),
        ("Hoy", datetime.date(2026, 11, 17)),
        ("ayer", datetime.date(2026, 11, 16)),
        ("Ayer.", datetime.date(2026, 11, 16)),
        ("anteayer", datetime.date(2026, 11, 15)),
        ("12/11", datetime.date(2026, 11, 12)),
        ("12/11/2025", datetime.date(2025, 11, 12)),
        ("1/3/2026", datetime.date(2026, 3, 1)),
        ("2026-11-12", datetime.date(2026, 11, 12)),
        ("12 de noviembre", datetime.date(2026, 11, 12)),
        ("3 de marzo de 2025", datetime.date(2025, 3, 3)),
        ("  el 12/11 ", datetime.date(2026, 11, 12)),
        ("1 de Septiembre", datetime.date(2026, 9, 1)),
        ("5 de setiembre", datetime.date(2026, 9, 5)),
    ],
)
def test_fechas_validas(texto, esperada):
    assert leer_fecha(texto, HOY) == esperada


@pytest.mark.parametrize("texto", ["el martes", "xx", "31/02", "", None, "12/13", "32 de enero"])
def test_fechas_que_no_se_entienden(texto):
    assert leer_fecha(texto, HOY) is None
