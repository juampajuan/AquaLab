from unittest import mock

import pytest
from django.contrib.messages import get_messages
from django.db import DatabaseError
from django.urls import reverse

from estudios.models import EstadoPruebaEstudio, Estudio

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


def test_generar_rechaza_si_hay_pruebas_sin_completar(cliente_http, estudio_de, completar):
    estudio = estudio_de("CL-", "PH", "CA")
    completar(estudio, "CL-")
    antes = estados(estudio)
    respuesta = generar(cliente_http, estudio)
    assert respuesta.status_code == 302
    assert respuesta["Location"] == reverse("informes:control", args=[estudio.pk])
    assert mensajes(respuesta) == [("error", "Hay 2 pruebas sin completar.")]
    assert estados(estudio) == antes


def test_generar_revalida_con_datos_vigentes(cliente_http, estudio_de, completar):
    estudio = estudio_de("CL-", "PH")
    completar(estudio)
    control = cliente_http.get(reverse("informes:control", args=[estudio.pk]))
    assert reverse("informes:generar", args=[estudio.pk]) in control.content.decode()
    # Una corrección (US 6.3) le quita la validación mientras el control sigue abierto.
    estudio.pruebas_asignadas.filter(prueba__codigo="PH").update(estado=EstadoPruebaEstudio.CARGADA)
    respuesta = generar(cliente_http, estudio)
    assert mensajes(respuesta) == [("error", "Hay 1 prueba sin completar.")]


def test_generar_listo_avisa_proximamente(cliente_http, estudio_de, completar):
    estudio = estudio_de("CL-", "PH")
    completar(estudio)
    antes = estados(estudio)
    respuesta = generar(cliente_http, estudio)
    assert respuesta.status_code == 302
    assert mensajes(respuesta) == [
        ("info", "La generación del informe estará disponible próximamente.")
    ]
    assert estados(estudio) == antes


def test_generar_con_informe_emitido_rechaza(cliente_http, estudio_de, completar, emitir):
    estudio = estudio_de("CL-")
    completar(estudio)
    emitir(estudio)
    respuesta = generar(cliente_http, estudio)
    assert mensajes(respuesta) == [("error", "El informe de este estudio ya fue generado.")]


def test_generar_solo_post(cliente_http, estudio_de):
    estudio = estudio_de("CL-")
    respuesta = cliente_http.get(reverse("informes:generar", args=[estudio.pk]))
    assert respuesta.status_code == 405


def test_generar_estudio_inexistente_404(cliente_http):
    respuesta = cliente_http.post(reverse("informes:generar", args=[999999]))
    assert respuesta.status_code == 404


def test_generar_error_de_base(cliente_http, estudio_de, completar):
    estudio = estudio_de("CL-")
    completar(estudio)
    with mock.patch("informes.servicios.comprobar_generacion", side_effect=DatabaseError):
        respuesta = generar(cliente_http, estudio)
    assert mensajes(respuesta) == [
        ("error", "No se pudo verificar el estudio. Intentá nuevamente.")
    ]
