"""US 6.6 – concurrencia de las curvas (research R5)."""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.utils import timezone

from pruebas import curvas
from pruebas.models import CurvaCalibracion

pytestmark = pytest.mark.django_db(transaction=True)

REFERENCIA = [
    ["0", "0.000"],
    ["0.1", "0.052"],
    ["0.2", "0.101"],
    ["0.3", "0.153"],
    ["0.4", "0.199"],
]


def en_hilo(funcion, usuario_id, barrera, **kwargs):
    close_old_connections()
    try:
        usuario = get_user_model().objects.get(pk=usuario_id)
        barrera.wait(timeout=10)
        try:
            return funcion(usuario=usuario, **kwargs)
        except curvas.CurvaError as exc:
            return exc
    finally:
        connection.close()


def datos():
    return {
        "fecha_preparacion": timezone.localdate().isoformat(),
        "observacion": "",
        "archivo_origen": "",
        "puntos": REFERENCIA,
    }


def test_concurrencia_guardar(administrador_catalogo, prueba_curva):
    """Dos confirmaciones simultáneas: dos curvas, una sola vigente (la última)."""
    barrera = threading.Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [
            pool.submit(
                en_hilo,
                curvas.guardar_curva,
                administrador_catalogo.pk,
                barrera,
                prueba_id=prueba_curva.pk,
                datos=datos(),
                clave=uuid.uuid4(),
            )
            for _ in range(2)
        ]
        resultados = [f.result(timeout=20) for f in futuros]
    assert all(isinstance(r, curvas.Guardado) for r in resultados)
    assert CurvaCalibracion.objects.count() == 2
    vigentes = CurvaCalibracion.objects.filter(vigente=True)
    assert vigentes.count() == 1
    assert vigentes.get() == CurvaCalibracion.objects.order_by("-fecha_carga", "-pk").first()


def test_concurrencia_misma_clave(administrador_catalogo, prueba_curva):
    """Doble envío de la misma confirmación: una sola curva."""
    clave = uuid.uuid4()
    barrera = threading.Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [
            pool.submit(
                en_hilo,
                curvas.guardar_curva,
                administrador_catalogo.pk,
                barrera,
                prueba_id=prueba_curva.pk,
                datos=datos(),
                clave=clave,
            )
            for _ in range(2)
        ]
        resultados = [f.result(timeout=20) for f in futuros]
    assert CurvaCalibracion.objects.count() == 1
    assert sorted(r.repetida for r in resultados) == [False, True]


def test_concurrencia_carga(administrador_catalogo, prueba_curva, estudio_de, empleado):
    """Una carga de medición y una curva nueva con «Calcularlas» a la vez: sin deadlock, la
    medición se calcula una sola vez y con una sola curva."""
    from decimal import Decimal

    from estudios.models import Resultado
    from estudios.servicios import CargarMedicionesError, cargar_mediciones
    from estudios.tests.utiles import asignacion_de, cargar

    estudio = estudio_de("NO2-C", "PH")
    cargar(estudio, empleado, {"NO2-C": "0.126"})  # espera curva
    ph = asignacion_de(estudio, "PH")
    barrera = threading.Barrier(2)

    def carga(usuario):
        return cargar_mediciones(estudio.pk, {ph.pk: Decimal("7")}, usuario)

    def en_hilo_carga(usuario_id):
        close_old_connections()
        try:
            usuario = get_user_model().objects.get(pk=usuario_id)
            barrera.wait(timeout=10)
            try:
                return carga(usuario)
            except CargarMedicionesError as exc:
                return exc
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [
            pool.submit(en_hilo_carga, empleado.pk),
            pool.submit(
                en_hilo,
                curvas.guardar_curva,
                administrador_catalogo.pk,
                barrera,
                prueba_id=prueba_curva.pk,
                datos=datos(),
                clave=uuid.uuid4(),
                calcular_pendientes=True,
            ),
        ]
        resultados = [f.result(timeout=30) for f in futuros]
    assert not any(isinstance(r, Exception) for r in resultados)
    no2 = Resultado.objects.filter(asignacion__prueba=prueba_curva)
    assert no2.count() == 1
    assert no2.get().curva == CurvaCalibracion.objects.get()
    assert Resultado.objects.filter(asignacion=ph).count() == 1


def test_concurrencia_borrar(administrador_catalogo, prueba_curva, curva_de, estudio_de, empleado):
    """Un recálculo que usa la curva vigente y un borrado a la vez: el borrado espera al lock y
    termina rechazado porque la curva quedó usada (sin IntegrityError por la FK)."""
    from estudios.servicios import cargar_mediciones
    from estudios.tests.utiles import asignacion_de

    curva = curva_de(prueba_curva)
    estudio = estudio_de("NO2-C")
    no2 = asignacion_de(estudio, "NO2-C")
    barrera = threading.Barrier(2)
    from decimal import Decimal

    def carga(usuario):
        return cargar_mediciones(estudio.pk, {no2.pk: Decimal("0.126")}, usuario)

    def en_hilo_carga(usuario_id):
        close_old_connections()
        try:
            usuario = get_user_model().objects.get(pk=usuario_id)
            barrera.wait(timeout=10)
            return carga(usuario)
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [
            pool.submit(en_hilo_carga, empleado.pk),
            pool.submit(
                en_hilo, curvas.borrar_curva, administrador_catalogo.pk, barrera, curva_id=curva.pk
            ),
        ]
        carga_hecha, borrado = [f.result(timeout=30) for f in futuros]
    from estudios.models import Resultado

    calculado = Resultado.objects.filter(asignacion=no2).first()
    if CurvaCalibracion.objects.filter(pk=curva.pk).exists():
        # La carga llegó primero: la curva quedó usada y el borrado se rechazó.
        assert isinstance(borrado, curvas.CurvaUsada)
        assert calculado.curva_id == curva.pk
    else:
        # El borrado llegó primero: la carga encontró la prueba sin curva.
        assert calculado is None
    assert carga_hecha.guardadas
