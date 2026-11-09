"""Comparación histórica con la demo de SCRUM-78 (US 8.1): valores esperados del Pozo 2 y el caso
Ausente/Presente del Tanque domiciliario (research R11 y R12).

Si un cambio del guion de la demo elimina alguno de estos casos, agregarlo de nuevo al guion
(`estudios/demo.py`) y a `test_demo.py` (CLAUDE.md, SCRUM-78).
"""

import re
from decimal import Decimal

import pytest

from estudios import comparacion
from estudios.models import EstadoPruebaEstudio, Estudio, PruebaEstudio, Validacion
from estudios.tests.test_demo import cargar, dia_2_del_mes, estudio
from muestras.models import Origen
from pruebas.limites import Evaluacion

pytestmark = pytest.mark.django_db


@pytest.fixture
def cargada(catalogo):
    ahora = dia_2_del_mes()
    cargar(ahora)
    return ahora


def de(historiales, codigo):
    (encontrado,) = [h for h in historiales if h.prueba.codigo == codigo]
    return encontrado


def test_pozo_2_cloruro_desde_estudio(cargada):
    actual = estudio(cargada, "Pozo 2", 0)

    cloruro = de(comparacion.comparar(actual.muestra.origen, estudio=actual), "CL-")

    assert [p.valor for p in cloruro.validados] == [
        Decimal("118"),
        Decimal("121"),
        Decimal("124"),
        Decimal("120"),
        Decimal("415"),
    ]
    fechas = [p.fecha_muestreo for p in cloruro.puntos]
    assert fechas == sorted(fechas)
    referencia = cloruro.referencia
    assert referencia.valor == Decimal("430")
    assert referencia.es_referencia and not referencia.validado
    assert cloruro.puntos[-1] is referencia
    assert cloruro.franja.maximo == Decimal("350")
    assert [p.evaluacion for p in cloruro.puntos][-2:] == [Evaluacion.FUERA_DE_NORMA] * 2
    assert cloruro.fuera_de_franja

    variacion = cloruro.variacion
    assert variacion.cantidad_anteriores == 5
    assert variacion.contra_anterior.texto == "+15 mg/l (+3,6 %)"
    assert variacion.promedio == Decimal("179.6")
    assert variacion.contra_promedio.texto == "+250,4 mg/l (+139,4 %)"


def test_pozo_2_cloruro_sin_referencia(cargada):
    origen = Origen.objects.get(nombre="Pozo 2")

    cloruro = de(comparacion.comparar(origen), "CL-")

    assert cloruro.referencia is None
    variacion = cloruro.variacion
    assert variacion.ultimo.valor == Decimal("415")
    assert variacion.contra_anterior.texto == "+295 mg/l (+245,8 %)"
    assert variacion.promedio == Decimal("120.75")
    assert variacion.contra_promedio.texto == "+294,25 mg/l (+243,7 %)"


def test_tanque_domiciliario_ecoli(cargada):
    origen = Origen.objects.get(nombre="Tanque domiciliario")

    ecoli = de(comparacion.comparar(origen), "ECOLI")

    assert ecoli.presencia
    assert ecoli.franja.presencia
    # Meses 5 a 1 (el mes 0 está Pendiente).
    assert [p.texto for p in ecoli.puntos] == [
        "Ausente",
        "Ausente",
        "Presente",
        "Ausente",
        "Ausente",
    ]
    assert ecoli.variacion.cambio_presencia == "Sin cambios (Ausente)"
    assert (ecoli.variacion.presentes, ecoli.variacion.cantidad_anteriores) == (1, 4)

    mes_3 = estudio(cargada, "Tanque domiciliario", 3)
    desde_mes_3 = de(comparacion.comparar(origen, estudio=mes_3), "ECOLI")

    assert desde_mes_3.referencia.texto == "Presente"
    assert desde_mes_3.variacion.cambio_presencia == "Cambió: Ausente → Presente"
    assert (desde_mes_3.variacion.presentes, desde_mes_3.variacion.cantidad_anteriores) == (0, 2)


def test_comparar_no_modifica(cargada):
    def estado():
        return (
            sorted(Estudio.objects.values_list("pk", "estado")),
            sorted(PruebaEstudio.objects.values_list("pk", "estado")),
            sorted(Validacion.objects.values_list("pk", "anulada")),
        )

    antes = estado()
    for origen in Origen.objects.all():
        comparacion.comparar(origen)
    actual = estudio(cargada, "Pozo 2", 0)
    comparacion.comparar(actual.muestra.origen, estudio=actual)

    assert estado() == antes
    assert PruebaEstudio.objects.filter(estado=EstadoPruebaEstudio.CARGADA).exists()


def test_vista_tanque_domiciliario(cargada, cliente_bioquimico):
    from django.urls import reverse

    origen = Origen.objects.get(nombre="Tanque domiciliario")
    url = f"{reverse('estudios:comparacion')}?cliente={origen.cliente_id}&origen={origen.pk}"

    html = cliente_bioquimico.get(url).content.decode()

    inicio = html.index('data-prueba="ECOLI"')
    ecoli = html[inicio : html.find("data-prueba=", inicio + 1)]
    assert "Sin cambios (Ausente)" in ecoli
    assert "Presente en 1 de 4" in ecoli
    tabla = ecoli[ecoli.index("<table") : ecoli.index("</table>")]
    resultados = re.findall(r'<td class="numeros">\s*(.*?)\s*</td>', tabla, re.S)
    celdas = [c.split()[0] for c in resultados]
    # Nunca 0 ni 1: Ausente/Presente, meses 5 a 1.
    assert celdas == ["Ausente", "Ausente", "Presente", "Ausente", "Ausente"]


def test_vista_pozo_2(cargada, cliente_bioquimico):
    from django.urls import reverse

    actual = estudio(cargada, "Pozo 2", 0)

    html = cliente_bioquimico.get(
        f"{reverse('estudios:comparacion')}?estudio={actual.pk}"
    ).content.decode()

    assert "▲ +15 mg/l (+3,6 %)" in html
    assert "Contra el promedio de 5 anteriores (179,6 mg/l)" in html
    assert "▲ +250,4 mg/l (+139,4 %)" in html
