import importlib

import pytest
from django.apps import apps
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from estudios.models import EstadoPruebaEstudio, Validacion
from estudios.servicios import ValidarResultadosError
from estudios.tests.utiles import asignacion_de, cargar, validar

pytestmark = pytest.mark.django_db

migracion = importlib.import_module("estudios.migrations.0008_grupo_bioquimicos")


def test_grupo_bioquimicos_tiene_el_permiso():
    # Los tests con transaction=True vacían la base: se ejecuta la migración de datos otra vez.
    Group.objects.filter(name="Bioquímicos").delete()
    migracion.crear_grupo(apps, None)
    migracion.crear_grupo(apps, None)  # idempotente
    grupo = Group.objects.get(name="Bioquímicos")
    assert list(grupo.permissions.values_list("content_type__app_label", "codename")) == [
        ("estudios", "validar_resultados")
    ]


def url(nombre, estudio):
    return reverse(f"estudios:{nombre}", args=[estudio.pk])


@pytest.fixture
def estudio_cargado(estudio_de, empleado):
    estudio = estudio_de("PH")
    cargar(estudio, empleado, PH="7.4")
    return estudio


def test_sin_permiso_no_ve_ni_valida(cliente_http, empleado, estudio_cargado):
    html = cliente_http.get(url("detalle", estudio_cargado)).content.decode()
    assert url("validar_resultados", estudio_cargado) not in html
    assert cliente_http.get(url("validar_resultados", estudio_cargado)).status_code == 403
    ph = asignacion_de(estudio_cargado, "PH")
    datos = {
        "accion": "confirmar",
        f"validar_{ph.pk}": "on",
        f"resultado_{ph.pk}": str(ph.resultado.valor),
    }
    assert cliente_http.post(url("validar_resultados", estudio_cargado), datos).status_code == 403
    with pytest.raises(
        ValidarResultadosError, match="Se requiere permiso para validar resultados."
    ):
        validar(estudio_cargado, empleado, "PH")
    assert not Validacion.objects.exists()
    assert asignacion_de(estudio_cargado, "PH").estado == EstadoPruebaEstudio.CARGADA


def test_bioquimico_ve_y_valida(cliente_bioquimico, estudio_cargado):
    html = cliente_bioquimico.get(url("detalle", estudio_cargado)).content.decode()
    assert url("validar_resultados", estudio_cargado) in html
    assert cliente_bioquimico.get(url("validar_resultados", estudio_cargado)).status_code == 200


def test_quien_cargo_puede_validar(estudio_cargado, empleado, bioquimico):
    """Sin doble control: el mismo usuario carga y valida (Clarifications)."""
    assert bioquimico == empleado
    resultado = validar(estudio_cargado, bioquimico, "PH")
    assert [p.codigo for p in resultado.validadas] == ["PH"]


def test_validar_requiere_sesion(estudio_cargado):
    respuesta = Client().get(url("validar_resultados", estudio_cargado))
    assert respuesta.status_code == 302
    assert respuesta.url.startswith(reverse("usuarios:login"))
