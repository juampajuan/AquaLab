"""Dos confirmaciones simultáneas con la misma clave mandan un solo correo (SCRUM-79, FR-010)."""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection

from estudios.tests.utiles import cargar, validar
from informes import envios
from informes.models import EnvioInforme
from informes.servicios import emitir_informe

pytestmark = pytest.mark.django_db(transaction=True)


def en_hilo(usuario_id, barrera, estudio_pk, clave):
    close_old_connections()
    try:
        usuario = get_user_model().objects.get(pk=usuario_id)
        barrera.wait(timeout=10)
        return envios.enviar_informe(estudio_pk, usuario, clave)
    finally:
        connection.close()


def test_doble_envio_concurrente(estudio_de, empleado, bioquimico, mailoutbox, monkeypatch):
    monkeypatch.setattr("informes.envios.generar_pdf", lambda informe: b"%PDF-falso")
    estudio = estudio_de("PH")
    cargar(estudio, empleado, PH="7.4")
    validar(estudio, bioquimico, "PH")
    emitir_informe(estudio.pk, bioquimico)
    clave = uuid.uuid4()
    barrera = threading.Barrier(2)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [
            pool.submit(en_hilo, bioquimico.pk, barrera, estudio.pk, clave) for _ in range(2)
        ]
        resultados = [f.result(timeout=15) for f in futuros]

    assert EnvioInforme.objects.filter(clave=clave).count() == 1
    assert len(mailoutbox) == 1
    assert sum(r.duplicado for r in resultados) == 1
