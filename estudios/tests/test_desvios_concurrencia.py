"""Concurrencia de la revisión de desvíos al validar (US 8.2): la constancia nace con la validación,
en su transacción y bajo el bloqueo del estudio."""

import datetime as dt
import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection

from estudios.models import Resultado, Validacion
from estudios.servicios import corregir_mediciones, validar_resultados
from estudios.tests.utiles import asignacion_de
from muestras.models import Origen

pytestmark = pytest.mark.django_db(transaction=True)

DIA = dt.date(2026, 3, 1)


def en_hilo(funcion, usuario_id, barrera, *args, **kwargs):
    close_old_connections()
    try:
        usuario = get_user_model().objects.get(pk=usuario_id)
        barrera.wait(timeout=10)
        return funcion(*args, usuario, **kwargs)
    finally:
        connection.close()


@pytest.fixture
def actual(cliente_a, estudio_en_origen):
    """Cloruro validado 100, 110, 120 y un estudio sin validar con Cloruro 160 (desvío)."""
    origen = Origen.objects.create(cliente=cliente_a, nombre="Pozo concurrente")
    for n, valor in enumerate(["10", "11", "12"]):
        estudio_en_origen(origen, DIA + dt.timedelta(days=n), 300901 + n, {"CL-": valor})
    return estudio_en_origen(
        origen, DIA + dt.timedelta(days=3), 300910, {"CL-": "16"}, validar_todo=False
    )


def test_dos_validaciones_simultaneas(actual, bioquimico, django_user_model):
    otro = django_user_model.objects.create_user(
        email="otro-bioquimico-desvios@ejemplo.com", password="Clave-Valida-123", is_active=True
    )
    otro.groups.set(bioquimico.groups.all())
    cl = asignacion_de(actual, "CL-")
    elegidas = {cl.pk: str(cl.resultado.valor)}
    barrera = threading.Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = {
            usuario.pk: pool.submit(
                en_hilo,
                validar_resultados,
                usuario.pk,
                barrera,
                actual.pk,
                elegidas,
                observaciones={cl.pk: f"Observación de {usuario.email}"},
            )
            for usuario in (bioquimico, otro)
        }
        resultados = {pk: f.result(timeout=15) for pk, f in futuros.items()}

    (validacion,) = Validacion.objects.filter(asignacion=cl)
    assert validacion.con_desvio and validacion.desvio_referencia == Decimal(110)
    ganador = get_user_model().objects.get(pk=validacion.validada_por_id)
    assert validacion.observacion == f"Observación de {ganador.email}"
    perdedor = next(r for pk, r in resultados.items() if pk != ganador.pk)
    assert [m for _, m in perdedor.omitidas] == ["ya estaba validada"]
    assert perdedor.con_desvio == []


def test_correccion_y_validacion_simultaneas(actual, bioquimico, empleado):
    cl = asignacion_de(actual, "CL-")
    barrera = threading.Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        validacion = pool.submit(
            en_hilo,
            validar_resultados,
            bioquimico.pk,
            barrera,
            actual.pk,
            {cl.pk: str(cl.resultado.valor)},
        )
        correccion = pool.submit(
            en_hilo,
            corregir_mediciones,
            empleado.pk,
            barrera,
            actual.pk,
            {cl.pk: (Decimal("16"), Decimal("20"))},
        )
        validacion.result(timeout=15)
        correccion.result(timeout=15)

    resultado = Resultado.objects.get(asignacion=cl)
    assert resultado.valor == Decimal(200)
    # Si la validación llegó primero, la corrección la anuló; si no, se omitió.
    assert not Validacion.objects.filter(asignacion=cl, anulada=False).exists()
    for anulada in Validacion.objects.filter(asignacion=cl, anulada=True):
        assert anulada.desvio_referencia == Decimal(110)
