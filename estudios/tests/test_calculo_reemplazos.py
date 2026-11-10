"""Cálculo de estudios anteriores a un reemplazo en cascada (SCRUM-73, FR-016c)."""

import uuid
from decimal import Decimal

import pytest

from estudios.models import TipoEstudio
from estudios.servicios import corregir_mediciones, crear_estudio
from estudios.tests.utiles import asignacion_de, cargar
from pruebas import gestion
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin(django_user_model):
    from django.contrib.auth.models import Group, Permission

    grupo, _ = Group.objects.get_or_create(name="Administradores")
    grupo.permissions.add(Permission.objects.get(codename="administrar_panel"))
    usuario = django_user_model.objects.create_user(email="adm@x.com", password="Clave-Valida-123")
    usuario.groups.add(grupo)
    return usuario


def reemplazar(admin, vieja, nueva):
    vieja.refresh_from_db()
    gestion.gestionar_prueba(
        usuario=admin,
        operacion="desactivar",
        prueba_id=vieja.pk,
        version_esperada=vieja.version,
        reemplazo_id=nueva.pk,
    )


def corregir(estudio, usuario, codigo, valor):
    asignacion = asignacion_de(estudio, codigo)
    corregir_mediciones(
        estudio.pk,
        {asignacion.pk: (str(asignacion.medicion.valor_ingresado), Decimal(valor))},
        usuario,
    )


@pytest.fixture
def con_x(muestra, empleado):
    x = Prueba.objects.create(codigo="X", nombre="Base", unidad="mg/l", unidad_medicion="mg/l")
    y = Prueba.objects.create(
        codigo="Y",
        nombre="Doble",
        unidad="mg/l",
        tipo_calculo="FORMULA",
        formula="{X}*2",
        es_calculada=True,
    )
    tipo = TipoEstudio.objects.create(nombre="X e Y")
    tipo.pruebas.set([x, y])
    datos = {
        "clave": str(uuid.uuid4()),
        "muestra": muestra.pk,
        "tipo": tipo.pk,
        "version": tipo.version,
    }
    estudio = crear_estudio(datos, empleado)
    cargar(estudio, empleado, X="5")
    return estudio, x, tipo


def test_recalculo_con_reemplazo(admin, con_x, empleado):
    estudio, x, _ = con_x
    assert asignacion_de(estudio, "Y").resultado.valor == Decimal("10")
    x2 = Prueba.objects.create(codigo="X2", nombre="Base nueva", unidad="mg/l")
    reemplazar(admin, x, x2)
    assert Prueba.objects.get(codigo="Y").formula == "{X2}*2"
    corregir(estudio, empleado, "X", "7")
    assert asignacion_de(estudio, "Y").resultado.valor == Decimal("14")


def test_estudio_nuevo_usa_reemplazo(admin, con_x, muestra, empleado):
    _, x, tipo = con_x
    x2 = Prueba.objects.create(codigo="X2", nombre="Base nueva", unidad="mg/l")
    reemplazar(admin, x, x2)
    tipo.refresh_from_db()
    datos = {
        "clave": str(uuid.uuid4()),
        "muestra": muestra.pk,
        "tipo": tipo.pk,
        "version": tipo.version,
    }
    nuevo = crear_estudio(datos, empleado)
    assert set(nuevo.pruebas_asignadas.values_list("prueba__codigo", flat=True)) == {"X2", "Y"}
    cargar(nuevo, empleado, X2="3")
    assert asignacion_de(nuevo, "Y").resultado.valor == Decimal("6")


def test_cadena(admin, con_x, empleado):
    estudio, x, _ = con_x
    x2 = Prueba.objects.create(codigo="X2", nombre="Base 2", unidad="mg/l")
    x3 = Prueba.objects.create(codigo="X3", nombre="Base 3", unidad="mg/l")
    reemplazar(admin, x, x2)
    reemplazar(admin, x2, x3)
    assert Prueba.objects.get(codigo="Y").formula == "{X3}*2"
    corregir(estudio, empleado, "X", "4")
    assert asignacion_de(estudio, "Y").resultado.valor == Decimal("8")
