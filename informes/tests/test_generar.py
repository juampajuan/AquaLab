from unittest import mock

import pytest
from django.contrib.messages import get_messages
from django.db import DatabaseError
from django.urls import reverse

from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Estudio
from informes.models import Informe

pytestmark = pytest.mark.django_db


def generar(cliente, estudio):
    return cliente.post(reverse("informes:generar", args=[estudio.pk]))


def mensajes(respuesta):
    return [(m.level_tag, str(m)) for m in get_messages(respuesta.wsgi_request)]


def estados(estudio):
    return (
        Estudio.objects.get(pk=estudio.pk).estado,
        sorted(estudio.pruebas_asignadas.values_list("pk", "estado")),
    )


def test_generar_rechaza_si_hay_pruebas_sin_completar(cliente_bioquimico, estudio_de, completar):
    estudio = estudio_de("CL-", "PH", "CA")
    completar(estudio, "CL-")
    antes = estados(estudio)
    respuesta = generar(cliente_bioquimico, estudio)
    assert respuesta.status_code == 302
    assert respuesta["Location"] == reverse("informes:control", args=[estudio.pk])
    assert mensajes(respuesta) == [("error", "Hay 2 pruebas sin completar.")]
    assert estados(estudio) == antes


def test_generar_revalida_con_datos_vigentes(cliente_bioquimico, estudio_de, completar):
    estudio = estudio_de("CL-", "PH")
    completar(estudio)
    control = cliente_bioquimico.get(reverse("informes:control", args=[estudio.pk]))
    assert reverse("informes:vista_previa", args=[estudio.pk]) in control.content.decode()
    # Una corrección (US 6.3) le quita la validación mientras el control sigue abierto.
    estudio.pruebas_asignadas.filter(prueba__codigo="PH").update(estado=EstadoPruebaEstudio.CARGADA)
    respuesta = generar(cliente_bioquimico, estudio)
    assert mensajes(respuesta) == [("error", "Hay 1 prueba sin completar.")]


def test_generar_listo_emite(cliente_bioquimico, estudio_de, completar):
    """US 7.2: con el estudio listo, generar emite el informe (antes avisaba «próximamente»)."""
    estudio = estudio_de("CL-", "PH")
    completar(estudio)
    respuesta = generar(cliente_bioquimico, estudio)
    assert respuesta.status_code == 302
    assert respuesta["Location"] == reverse("informes:ver", args=[estudio.pk])
    assert mensajes(respuesta) == [
        ("success", f"Se emitió el informe INF-000001 del estudio {estudio.pk}.")
    ]
    assert Informe.objects.filter(estudio=estudio).exists()
    assert Estudio.objects.get(pk=estudio.pk).estado == EstadoEstudio.INFORME_GENERADO


def test_generar_con_informe_emitido_rechaza(cliente_bioquimico, estudio_de, completar, emitir):
    estudio = estudio_de("CL-")
    completar(estudio)
    emitir(estudio)
    respuesta = generar(cliente_bioquimico, estudio)
    assert mensajes(respuesta) == [("error", "El informe de este estudio ya fue generado.")]


def test_generar_solo_post(cliente_bioquimico, estudio_de):
    estudio = estudio_de("CL-")
    respuesta = cliente_bioquimico.get(reverse("informes:generar", args=[estudio.pk]))
    assert respuesta.status_code == 405


def test_generar_estudio_inexistente_404(cliente_bioquimico):
    respuesta = cliente_bioquimico.post(reverse("informes:generar", args=[999999]))
    assert respuesta.status_code == 404


def test_generar_error_de_base(cliente_bioquimico, estudio_de, completar):
    estudio = estudio_de("CL-")
    completar(estudio)
    with mock.patch("informes.servicios.emitir_informe", side_effect=DatabaseError):
        respuesta = generar(cliente_bioquimico, estudio)
    assert mensajes(respuesta) == [("error", "No se pudo emitir el informe. Intentá nuevamente.")]
