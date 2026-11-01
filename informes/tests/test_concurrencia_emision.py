import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection

from estudios.tests.utiles import cargar, validar
from informes.models import Informe
from informes.servicios import InformeNoDisponible, emitir_informe

pytestmark = pytest.mark.django_db(transaction=True)


def en_hilo(usuario_id, barrera, estudio_pk):
    close_old_connections()
    try:
        usuario = get_user_model().objects.get(pk=usuario_id)
        barrera.wait(timeout=10)
        try:
            return emitir_informe(estudio_pk, usuario)
        except InformeNoDisponible as exc:
            return exc
    finally:
        connection.close()


def test_emisiones_concurrentes(estudio_de, empleado, bioquimico, django_user_model):
    otro = django_user_model.objects.create_user(
        email="otro-bioquimico-emision@ejemplo.com", password="Clave-Valida-123", is_active=True
    )
    otro.groups.set(bioquimico.groups.all())
    estudio = estudio_de("PH")
    cargar(estudio, empleado, PH="7.4")
    validar(estudio, bioquimico, "PH")
    barrera = threading.Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [
            pool.submit(en_hilo, usuario.pk, barrera, estudio.pk) for usuario in (bioquimico, otro)
        ]
        resultados = [f.result(timeout=15) for f in futuros]
    assert Informe.objects.filter(estudio=estudio).count() == 1
    assert sum(isinstance(r, Informe) for r in resultados) == 1
    rechazo = next(r for r in resultados if isinstance(r, InformeNoDisponible))
    assert str(rechazo) == "El informe de este estudio ya fue generado."
