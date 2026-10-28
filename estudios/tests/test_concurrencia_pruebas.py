import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection

from estudios.servicios import GestionPruebasError, agregar_prueba

pytestmark = pytest.mark.django_db(transaction=True)


def en_hilo(operacion, estudio_pk, objetivo_pk, usuario_id, barrera):
    close_old_connections()
    try:
        usuario = get_user_model().objects.get(pk=usuario_id)
        barrera.wait(timeout=10)
        try:
            return operacion(estudio_pk, objetivo_pk, usuario)
        except GestionPruebasError as exc:
            return exc
    finally:
        connection.close()


def simultaneas(operacion, estudio, objetivos, usuario):
    barrera = threading.Barrier(len(objetivos))
    with ThreadPoolExecutor(max_workers=len(objetivos)) as pool:
        futuros = [
            pool.submit(en_hilo, operacion, estudio.pk, pk, usuario.pk, barrera) for pk in objetivos
        ]
        return [f.result(timeout=15) for f in futuros]


def test_agregados_concurrentes_no_duplican(estudio, prueba_extra, empleado):
    from estudios.servicios import PruebaYaAsignada

    resultados = simultaneas(agregar_prueba, estudio, [prueba_extra.pk] * 2, empleado)
    assert sum(isinstance(r, PruebaYaAsignada) for r in resultados) == 1
    assert estudio.pruebas_asignadas.filter(prueba=prueba_extra).count() == 1
