import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection

from estudios.models import Validacion
from estudios.servicios import validar_resultados
from estudios.tests.utiles import asignacion_de, cargar

pytestmark = pytest.mark.django_db(transaction=True)


def en_hilo(usuario_id, barrera, estudio_pk, elegidas):
    close_old_connections()
    try:
        usuario = get_user_model().objects.get(pk=usuario_id)
        barrera.wait(timeout=10)
        return validar_resultados(estudio_pk, elegidas, usuario)
    finally:
        connection.close()


def test_validaciones_concurrentes(estudio_de, empleado, bioquimico, django_user_model):
    otro = django_user_model.objects.create_user(
        email="otro-bioquimico-concurrencia@ejemplo.com",
        password="Clave-Valida-123",
        is_active=True,
    )
    otro.groups.set(bioquimico.groups.all())
    estudio = estudio_de("PH")
    cargar(estudio, empleado, PH="7.4")
    ph = asignacion_de(estudio, "PH")
    elegidas = {ph.pk: str(ph.resultado.valor)}
    barrera = threading.Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [
            pool.submit(en_hilo, usuario.pk, barrera, estudio.pk, elegidas)
            for usuario in (bioquimico, otro)
        ]
        resultados = [f.result(timeout=15) for f in futuros]
    assert Validacion.objects.filter(asignacion=ph).count() == 1
    assert sorted((len(r.validadas), len(r.omitidas)) for r in resultados) == [(0, 1), (1, 0)]
    omitida = next(r for r in resultados if r.omitidas)
    assert omitida.omitidas[0][1] == "ya estaba validada"
