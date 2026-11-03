from datetime import date

import pytest

from clientes.models import Cliente
from informes.busqueda import informes_emitidos

pytestmark = pytest.mark.django_db


def numeros(qs):
    return [i.numero for i in qs]


@pytest.mark.parametrize("q", ["INF-000002", "inf-2", "INF2", "2", "0002"])
def test_busca_por_numero(tres_informes, q):
    assert numeros(informes_emitidos(q, None, None)) == [2]


@pytest.mark.parametrize(("q", "esperado"), [("nunez", [2]), ("JOSÉ", [2]), ("aguas del", [3, 1])])
def test_busca_por_cliente(tres_informes, q, esperado):
    assert numeros(informes_emitidos(q, None, None)) == esperado


def test_busca_por_documento(tres_informes):
    assert numeros(informes_emitidos("4445", None, None)) == [2]
    assert numeros(informes_emitidos("30712345679", None, None)) == [3]
    assert numeros(informes_emitidos("307123", None, None)) == [3, 1]


def test_busca_por_numero_pi(tres_informes):
    assert numeros(informes_emitidos("200102", None, None)) == [2]


def test_busca_por_datos_guardados(tres_informes):
    Cliente.objects.filter(nombre="José Núñez").update(nombre="Pedro Gómez")
    assert numeros(informes_emitidos("nunez", None, None)) == [2]
    assert numeros(informes_emitidos("gomez", None, None)) == []


def test_filtra_por_fechas(tres_informes, con_fecha):
    uno, dos, tres = tres_informes
    con_fecha(uno, 2026, 10, 1)
    con_fecha(dos, 2026, 10, 5, hora=23, minuto=30)
    con_fecha(tres, 2026, 10, 9)
    assert numeros(informes_emitidos("", date(2026, 10, 5), None)) == [3, 2]
    assert numeros(informes_emitidos("", None, date(2026, 10, 5))) == [2, 1]
    assert numeros(informes_emitidos("", date(2026, 10, 5), date(2026, 10, 5))) == [2]
    assert numeros(informes_emitidos("", date(2026, 10, 1), date(2026, 10, 9))) == [3, 2, 1]
    assert numeros(informes_emitidos("", date(2026, 10, 6), date(2026, 10, 8))) == []


def test_fechas_y_busqueda_combinadas(tres_informes, con_fecha):
    uno, dos, tres = tres_informes
    con_fecha(uno, 2026, 10, 1)
    con_fecha(dos, 2026, 10, 5)
    con_fecha(tres, 2026, 10, 9)
    assert numeros(informes_emitidos("aguas", date(2026, 10, 2), None)) == [3]


def test_orden_mas_reciente_primero(tres_informes):
    assert numeros(informes_emitidos("", None, None)) == [3, 2, 1]
