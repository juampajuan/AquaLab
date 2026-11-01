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


def test_cargas_concurrentes_calculan_una_vez(estudio_de, empleado):
    from estudios.models import Resultado
    from estudios.tests.utiles import asignacion_de

    estudio = estudio_de("CA", "DUREZA-T", "MG")
    barrera = threading.Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [
            pool.submit(
                en_hilo,
                cargar_mediciones,
                empleado.pk,
                barrera,
                estudio.pk,
                {asignacion_de(estudio, codigo).pk: Decimal(valor)},
            )
            for codigo, valor in (("CA", "80"), ("DUREZA-T", "15"))
        ]
        for futuro in futuros:
            futuro.result(timeout=15)
    mg = asignacion_de(estudio, "MG")
    assert Resultado.objects.filter(asignacion=mg).count() == 1
    assert mg.resultado.valor == Decimal("24.3")
    assert mg.estado == EstadoPruebaEstudio.CARGADA


def test_correcciones_concurrentes(estudio_de, empleado):
    from estudios.models import Medicion
    from estudios.servicios import corregir_mediciones
    from estudios.tests.utiles import asignacion_de, cargar

    estudio = estudio_de("CA", "DUREZA-T", "MG")
    cargar(estudio, empleado, CA="80", DUREZA_T="15")
    ca = asignacion_de(estudio, "CA")
    barrera = threading.Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [
            pool.submit(
                en_hilo,
                corregir_mediciones,
                empleado.pk,
                barrera,
                estudio.pk,
                {ca.pk: (Decimal("80"), Decimal(valor))},
            )
            for valor in ("50", "60")
        ]
        resultados = [f.result(timeout=15) for f in futuros]
    final = Medicion.objects.get(asignacion=ca).valor
    assert final in (Decimal("50"), Decimal("60"))
    assert sorted(len(r.corregidas) for r in resultados) == [0, 1]
    omitida = next(r for r in resultados if not r.corregidas)
    assert [(p.codigo, m) for p, m in omitida.omitidas] == [("CA", "cambió mientras se editaba")]
    mg = asignacion_de(estudio, "MG")
    assert mg.resultado.valor == (Decimal("300") - final * Decimal("2.5")) * Decimal("0.243")
