from unittest import mock

import pytest
from django.contrib.messages import get_messages
from django.db import DatabaseError
from django.urls import reverse

from estudios.tests.utiles import cargar, validar
from informes.models import Informe

pytestmark = pytest.mark.django_db


def mensajes(respuesta):
    return [str(m) for m in get_messages(respuesta.wsgi_request)]


def emitir(cliente, estudio):
    return cliente.post(reverse("informes:generar", args=[estudio.pk]))


@pytest.fixture
def estudio_listo(estudio_de, empleado, bioquimico):
    estudio = estudio_de("PH")
    cargar(estudio, empleado, PH="7.4")
    validar(estudio, bioquimico, "PH")
    return estudio


def test_emitir_redirige_al_informe(cliente_bioquimico, estudio_listo):
    respuesta = emitir(cliente_bioquimico, estudio_listo)
    assert respuesta.status_code == 302
    assert respuesta["Location"] == reverse("informes:ver", args=[estudio_listo.pk])
    assert mensajes(respuesta) == [
        f"Se emitió el informe INF-000001 del estudio {estudio_listo.pk}."
    ]


def test_emitir_no_listo_vuelve_al_control(cliente_bioquimico, estudio_de):
    estudio = estudio_de("PH")
    respuesta = emitir(cliente_bioquimico, estudio)
    assert respuesta["Location"] == reverse("informes:control", args=[estudio.pk])
    assert mensajes(respuesta) == ["Hay 1 prueba sin completar."]
    assert not Informe.objects.exists()


def test_sin_permiso_403(cliente_http, estudio_listo, django_user_model):
    from django.test import Client

    comun = django_user_model.objects.create_user(
        email="comun-vista@ejemplo.com", password="Clave-Valida-123", is_active=True
    )
    cliente = Client()
    cliente.force_login(comun)
    assert emitir(cliente, estudio_listo).status_code == 403
    assert not Informe.objects.exists()


def test_emitir_requiere_post(cliente_bioquimico, estudio_listo):
    url = reverse("informes:generar", args=[estudio_listo.pk])
    assert cliente_bioquimico.get(url).status_code == 405


def test_error_de_base_al_emitir(cliente_bioquimico, estudio_listo):
    with mock.patch("informes.servicios.emitir_informe", side_effect=DatabaseError):
        respuesta = emitir(cliente_bioquimico, estudio_listo)
    assert respuesta["Location"] == reverse("informes:control", args=[estudio_listo.pk])
    assert mensajes(respuesta) == ["No se pudo emitir el informe. Intentá nuevamente."]
    assert not Informe.objects.exists()
