import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from estudios.models import EstadoPruebaEstudio, Estudio
from informes.servicios import (
    InformeNoDisponible,
    comprobar_generacion,
    estudios_para_informar,
    motivo_para_no_informar,
)

pytestmark = pytest.mark.django_db


def preparar(estudio_de, completar, emitir, caso):
    """Un estudio en cada situación de la tabla de data-model.md."""
    if caso == "emitido":
        estudio = estudio_de("CL-", "PH")
        completar(estudio)
        emitir(estudio)
    elif caso == "sin_pruebas":
        estudio = estudio_de("CL-")
        estudio.pruebas_asignadas.all().delete()
    elif caso == "una_de_dos":
        estudio = estudio_de("CL-", "PH")
        completar(estudio, "CL-")
    elif caso == "ninguna_de_tres":
        estudio = estudio_de("CL-", "PH", "CA")
    else:
        estudio = estudio_de("CL-", "PH")
        completar(estudio)
    return Estudio.objects.get(pk=estudio.pk)


CASOS = [
    ("emitido", "El informe de este estudio ya fue generado."),
    ("sin_pruebas", "El estudio no tiene pruebas."),
    ("una_de_dos", "Hay 1 prueba sin completar."),
    ("ninguna_de_tres", "Hay 3 pruebas sin completar."),
    ("listo", None),
]


@pytest.mark.parametrize(("caso", "esperado"), CASOS)
def test_motivo_para_no_informar(estudio_de, completar, emitir, caso, esperado):
    estudio = preparar(estudio_de, completar, emitir, caso)
    assert motivo_para_no_informar(estudio, list(estudio.pruebas_asignadas.all())) == esperado


def test_cargadas_cuentan_como_sin_completar(estudio_de, completar):
    estudio = estudio_de("CL-", "PH")
    completar(estudio, "PH")
    estudio.pruebas_asignadas.filter(prueba__codigo="CL-").update(
        estado=EstadoPruebaEstudio.CARGADA
    )
    asignaciones = list(estudio.pruebas_asignadas.all())
    assert motivo_para_no_informar(estudio, asignaciones) == "Hay 1 prueba sin completar."


def test_comprobar_generacion_ok(estudio_de, completar):
    estudio = estudio_de("CL-", "PH")
    completar(estudio)
    assert comprobar_generacion(estudio.pk) == estudio


def test_comprobar_generacion_rechaza(estudio_de, completar):
    estudio = estudio_de("CL-", "PH")
    completar(estudio, "CL-")
    with pytest.raises(InformeNoDisponible, match="Hay 1 prueba sin completar."):
        comprobar_generacion(estudio.pk)


def test_comprobar_generacion_bloquea_estudio(estudio_de, completar):
    estudio = estudio_de("CL-")
    completar(estudio)
    with CaptureQueriesContext(connection) as consultas:
        comprobar_generacion(estudio.pk)
    assert any("estudios_estudio" in c["sql"] and "FOR UPDATE" in c["sql"] for c in consultas)


def test_estudios_para_informar_anota_avance(estudio_de, completar):
    estudio = estudio_de("CL-", "PH", "CA")
    completar(estudio, "PH")
    anotado = estudios_para_informar("", solo_listos=False).get(pk=estudio.pk)
    assert anotado.total_pruebas == 3
    assert anotado.pruebas_completadas == 1


def test_filtro_listos_coincide_con_la_regla(estudio_de, completar, emitir):
    estudios = [preparar(estudio_de, completar, emitir, caso) for caso, _ in CASOS]
    listos = {e.pk for e in estudios_para_informar("", solo_listos=True)}
    por_regla = {
        e.pk
        for e in estudios
        if motivo_para_no_informar(e, list(e.pruebas_asignadas.all())) is None
    }
    assert listos == por_regla
    assert len(listos) == 1
