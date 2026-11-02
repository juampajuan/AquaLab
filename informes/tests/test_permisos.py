import importlib

import pytest
from django.apps import apps
from django.contrib.auth.models import Group

pytestmark = pytest.mark.django_db

migracion = importlib.import_module("informes.migrations.0002_permiso_bioquimicos")


def test_grupo_bioquimicos_puede_emitir():
    # Los tests con transaction=True vacían la base: se ejecuta la migración de datos otra vez.
    Group.objects.filter(name="Bioquímicos").delete()
    migracion.asignar_permiso(apps, None)
    migracion.asignar_permiso(apps, None)  # idempotente
    grupo = Group.objects.get(name="Bioquímicos")
    assert ("informes", "emitir_informes") in grupo.permissions.values_list(
        "content_type__app_label", "codename"
    )


@pytest.fixture
def estudio_listo(estudio_de, empleado, bioquimico):
    from estudios.tests.utiles import cargar, validar

    estudio = estudio_de("PH")
    cargar(estudio, empleado, PH="7.4")
    validar(estudio, bioquimico, "PH")
    return estudio


@pytest.fixture
def comun(django_user_model):
    return django_user_model.objects.create_user(
        email="comun-permisos-informe@ejemplo.com", password="Clave-Valida-123", is_active=True
    )


def test_sin_permiso_no_emite(estudio_listo, comun):
    from django.test import Client
    from django.urls import reverse

    from informes.models import Informe
    from informes.servicios import EmitirInformeError, emitir_informe

    cliente = Client()
    cliente.force_login(comun)
    accion = reverse("informes:generar", args=[estudio_listo.pk])
    previa = cliente.get(reverse("informes:vista_previa", args=[estudio_listo.pk]))
    assert previa.status_code == 200
    assert f'action="{accion}"' not in previa.content.decode()
    assert cliente.post(accion).status_code == 403
    with pytest.raises(EmitirInformeError):
        emitir_informe(estudio_listo.pk, comun)
    assert not Informe.objects.exists()


def test_agregado_al_grupo_emite(estudio_listo, comun):
    from informes.servicios import emitir_informe

    comun.groups.add(Group.objects.get(name="Bioquímicos"))
    comun = type(comun).objects.get(pk=comun.pk)  # sin la caché de permisos
    assert emitir_informe(estudio_listo.pk, comun).numero == 1
