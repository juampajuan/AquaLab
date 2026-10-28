import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection

from estudios.servicios import PruebaYaAsignada, agregar_prueba

pytestmark = pytest.mark.django_db(transaction=True)


def ejecutar(estudio_pk, prueba_pk, usuario_id, barrera):
    close_old_connections()
    try:
        usuario = get_user_model().objects.get(pk=usuario_id)
        barrera.wait(timeout=10)
        try:
            return agregar_prueba(estudio_pk, prueba_pk, usuario).pk
        except PruebaYaAsignada as exc:
            return exc
    finally:
        connection.close()


def test_agregados_concurrentes_no_duplican(estudio, prueba_extra, empleado):
    barrera = threading.Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [
            pool.submit(ejecutar, estudio.pk, prueba_extra.pk, empleado.pk, barrera)
            for _ in range(2)
        ]
        resultados = [f.result(timeout=15) for f in futuros]
    assert sum(isinstance(r, int) for r in resultados) == 1
    assert sum(isinstance(r, PruebaYaAsignada) for r in resultados) == 1
    assert estudio.pruebas_asignadas.filter(prueba=prueba_extra).count() == 1
