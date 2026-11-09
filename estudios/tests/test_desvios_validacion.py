"""Constancia del desvío en la validación (US 8.2): `Validacion.observacion`, `desvio_referencia` y
`desvio_umbral`."""

import datetime as dt
from decimal import Decimal
from unittest import mock

import pytest
from django.db import DatabaseError, IntegrityError, transaction

from estudios import desvios
from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Validacion
from estudios.servicios import corregir_mediciones, validar_resultados
from estudios.tests.utiles import asignacion_de, validar
from muestras.models import Origen

pytestmark = pytest.mark.django_db

DIA = dt.date(2026, 3, 1)


def dia(n):
    return DIA + dt.timedelta(days=n)


@pytest.fixture
def origen(cliente_a):
    return Origen.objects.create(cliente=cliente_a, nombre="Pozo de desvíos")


def test_restriccion_desvio_completo(origen, estudio_en_origen):
    estudio = estudio_en_origen(origen, dia(0), 300201, {"CL-": "10"})
    validacion = Validacion.objects.get(asignacion__estudio=estudio)
    assert validacion.observacion == ""
    assert validacion.desvio_referencia is None and validacion.desvio_umbral is None
    assert not validacion.con_desvio

    for campos in ({"desvio_referencia": Decimal(110)}, {"desvio_umbral": Decimal(30)}):
        with pytest.raises(IntegrityError), transaction.atomic():
            Validacion.objects.filter(pk=validacion.pk).update(**campos)

    Validacion.objects.filter(pk=validacion.pk).update(
        desvio_referencia=Decimal(110), desvio_umbral=Decimal(30), observacion="Repetida"
    )
    validacion.refresh_from_db()
    assert validacion.con_desvio


# --- Constancia al validar (US 3, FR-009) ----------------------------------------------------


@pytest.fixture
def historia(origen, estudio_en_origen):
    """Cloruro validado 100, 110 y 120 mg/l y pH 7,0 en tres muestras anteriores."""
    for n, valor in enumerate(["10", "11", "12"]):
        estudio_en_origen(origen, dia(n), 300701 + n, {"CL-": valor, "PH": "7.0"})


@pytest.fixture
def actual(origen, historia, estudio_en_origen):
    """Sin validar: Cloruro 160 (desvío, mediana 110) y pH 7,1 (sin desvío)."""
    return estudio_en_origen(origen, dia(3), 300710, {"CL-": "16", "PH": "7.1"}, validar_todo=False)


def vigente(estudio, codigo):
    return Validacion.objects.get(asignacion=asignacion_de(estudio, codigo), anulada=False)


def test_constancia_al_validar(actual, bioquimico):
    resultado = validar(actual, bioquimico, "CL-", observaciones={"CL-": "  Repetida  "})
    validacion = vigente(actual, "CL-")
    assert validacion.observacion == "Repetida"
    assert validacion.desvio_referencia == Decimal(110)
    assert validacion.desvio_umbral == Decimal(30)
    assert validacion.validada_por == bioquimico
    assert [p.codigo for p in resultado.con_desvio] == ["CL-"]
    assert not [p for p in desvios.pendientes() if p.asignacion.estudio_id == actual.pk]


def test_sin_desvio_sin_constancia(actual, bioquimico):
    validar(actual, bioquimico, "PH", observaciones={"PH": "Nota"})
    validacion = vigente(actual, "PH")
    assert validacion.observacion == "Nota"
    assert validacion.desvio_referencia is None and not validacion.con_desvio


def test_no_elegida_no_guarda(actual, bioquimico):
    validar(actual, bioquimico, "PH", observaciones={"CL-": "No se guarda"})
    cl = asignacion_de(actual, "CL-")
    assert cl.estado == EstadoPruebaEstudio.CARGADA
    assert not Validacion.objects.filter(asignacion=cl).exists()
    assert [p.asignacion.pk for p in desvios.pendientes()] == [cl.pk]


def test_omitida_no_guarda(actual, bioquimico):
    cl = asignacion_de(actual, "CL-")
    resultado = validar_resultados(
        actual.pk, {cl.pk: "999"}, bioquimico, observaciones={cl.pk: "Vieja"}
    )
    assert [(p.codigo, motivo) for p, motivo in resultado.omitidas] == [
        ("CL-", "cambió mientras se revisaba")
    ]
    assert not Validacion.objects.filter(asignacion=cl).exists()

    validar(actual, bioquimico, "CL-", observaciones={"CL-": "Primera"})
    otra = validar(actual, bioquimico, "CL-", observaciones={"CL-": "Segunda"})
    assert [motivo for _, motivo in otra.omitidas] == ["ya estaba validada"]
    assert vigente(actual, "CL-").observacion == "Primera"
    assert Validacion.objects.filter(asignacion=cl).count() == 1


def test_validacion_fallida_no_guarda(actual, bioquimico):
    cl = asignacion_de(actual, "CL-")
    with mock.patch("estudios.calculo.cambiar_estado", side_effect=DatabaseError("falla")):
        with pytest.raises(DatabaseError):
            validar(actual, bioquimico, "CL-", observaciones={"CL-": "No queda"})
    assert not Validacion.objects.filter(asignacion=cl).exists()


def test_constancia_inalterable(origen, actual, bioquimico, estudio_en_origen, settings):
    validar(actual, bioquimico, "CL-")
    antes = vigente(actual, "CL-")
    estudio_en_origen(origen, dia(4), 300711, {"CL-": "30"})
    settings.AQUALAB_DESVIOS = {"umbral": "50", "cantidad": 2}
    despues = vigente(actual, "CL-")
    assert (despues.desvio_referencia, despues.desvio_umbral) == (
        antes.desvio_referencia,
        antes.desvio_umbral,
    )


def test_correccion_posterior(actual, bioquimico, empleado):
    validar(actual, bioquimico, "CL-", observaciones={"CL-": "Repetida"})
    cl = asignacion_de(actual, "CL-")
    corregir_mediciones(actual.pk, {cl.pk: (Decimal("16"), Decimal("17"))}, empleado)
    anulada = Validacion.objects.get(asignacion=cl, anulada=True)
    assert anulada.observacion == "Repetida" and anulada.desvio_referencia == Decimal(110)
    pendientes = [p for p in desvios.pendientes() if p.asignacion.pk == cl.pk]
    assert pendientes and pendientes[0].deteccion.valor == Decimal(170)


def test_evalua_al_confirmar(origen, actual, bioquimico, estudio_en_origen):
    """El historial cambia después de abrir la pantalla: vale la evaluación al confirmar."""
    cl = asignacion_de(actual, "CL-")
    elegidas = {cl.pk: str(cl.resultado.valor)}  # lo que se vio al abrir
    # Llegan dos validados de 160 anteriores a la muestra (mismo día que el último previo, N° PI
    # mayor): los últimos 3 son 120, 160 y 160, la mediana pasa a 160 y ya no es desvío.
    estudio_en_origen(origen, dia(2), 300712, {"CL-": "16"})
    estudio_en_origen(origen, dia(2), 300713, {"CL-": "16"})
    resultado = validar_resultados(actual.pk, elegidas, bioquimico)
    assert resultado.con_desvio == []
    assert not vigente(actual, "CL-").con_desvio


def test_validar_con_desvio_sin_observacion(actual, bioquimico):
    valor = asignacion_de(actual, "CL-").resultado.valor
    validar(actual, bioquimico, "CL-", "PH")
    cl = asignacion_de(actual, "CL-")
    assert cl.resultado.valor == valor
    assert cl.estado == EstadoPruebaEstudio.COMPLETADA
    actual.refresh_from_db()
    assert actual.estado == EstadoEstudio.FINALIZADO
    validacion = vigente(actual, "CL-")
    assert validacion.con_desvio and validacion.observacion == ""
