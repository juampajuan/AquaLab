import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection

from estudios.models import EstadoPruebaEstudio, Medicion, PruebaEstudio
from estudios.servicios import GestionPruebasError, cargar_mediciones, quitar_prueba

pytestmark = pytest.mark.django_db(transaction=True)


def en_hilo(funcion, usuario_id, barrera, *args):
    close_old_connections()
    try:
        usuario = get_user_model().objects.get(pk=usuario_id)
        barrera.wait(timeout=10)
        try:
            return funcion(*args, usuario)
        except GestionPruebasError as exc:
            return exc
    finally:
        connection.close()


def test_cargas_concurrentes_misma_prueba(estudio_mediciones, asignaciones_medicion, empleado):
    ph = asignaciones_medicion["TEST-PH"]
    barrera = threading.Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [
            pool.submit(
                en_hilo,
                cargar_mediciones,
                empleado.pk,
                barrera,
                estudio_mediciones.pk,
                {ph.pk: Decimal(valor)},
            )
            for valor in ("1.1", "2.2")
        ]
        resultados = [f.result(timeout=15) for f in futuros]
    assert Medicion.objects.filter(asignacion=ph).count() == 1
    assert sorted((len(r.guardadas), len(r.omitidas)) for r in resultados) == [(0, 1), (1, 0)]


def test_carga_y_quita_concurrentes(estudio_mediciones, asignaciones_medicion, empleado):
    ph = asignaciones_medicion["TEST-PH"]
    barrera = threading.Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        carga = pool.submit(
            en_hilo,
            cargar_mediciones,
            empleado.pk,
            barrera,
            estudio_mediciones.pk,
            {ph.pk: Decimal("7")},
        )
        quita = pool.submit(
            en_hilo, quitar_prueba, empleado.pk, barrera, estudio_mediciones.pk, ph.pk
        )
        carga.result(timeout=15)
        quita.result(timeout=15)
    asignacion = PruebaEstudio.objects.filter(pk=ph.pk).first()
    if asignacion is None:
        assert not Medicion.objects.exists()
    else:
        assert asignacion.estado == EstadoPruebaEstudio.CARGADA
        assert Medicion.objects.filter(asignacion=asignacion).count() == 1
