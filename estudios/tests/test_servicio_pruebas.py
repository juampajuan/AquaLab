import uuid

import pytest

from estudios.models import Estudio, PruebaEstudio
from estudios.servicios import (
    GestionPruebasError,
    PruebaYaAsignada,
    agregar_prueba,
    crear_estudio,
)

pytestmark = pytest.mark.django_db

CAMPOS_CABECERA = (
    "muestra_id",
    "tipo_id",
    "estado",
    "creado_por_id",
    "fecha_creacion",
    "tipo_nombre_snapshot",
    "tipo_descripcion_snapshot",
    "tipo_version_snapshot",
)


def codigos(estudio):
    return set(estudio.pruebas_asignadas.values_list("prueba__codigo", flat=True))


def capturar_estado(estudio, otro):
    estudio.refresh_from_db()
    estudio.tipo.refresh_from_db()
    return {
        "cabecera": {campo: getattr(estudio, campo) for campo in CAMPOS_CABECERA},
        "tipo_pruebas": set(estudio.tipo.pruebas.values_list("pk", flat=True)),
        "tipo_version": estudio.tipo.version,
        "otro": codigos(otro),
    }


@pytest.fixture
def otro_estudio(datos, empleado):
    return crear_estudio({**datos, "clave": str(uuid.uuid4())}, empleado)


def test_agregar_prueba_crea_asignacion(estudio, prueba_extra, empleado):
    asignacion = agregar_prueba(estudio.pk, prueba_extra.pk, empleado)
    assert isinstance(asignacion, PruebaEstudio)
    assert codigos(estudio) == {"TEST-A", "TEST-B", "TEST-C"}


def test_agregar_no_modifica_cabecera_tipo_ni_otros_estudios(
    estudio, otro_estudio, prueba_extra, empleado
):
    antes = capturar_estado(estudio, otro_estudio)
    agregar_prueba(estudio.pk, prueba_extra.pk, empleado)
    assert capturar_estado(estudio, otro_estudio) == antes


def test_agregar_prueba_ya_asignada_rechazada(estudio, pruebas, empleado):
    with pytest.raises(PruebaYaAsignada, match="TEST-A ya forma parte del estudio"):
        agregar_prueba(estudio.pk, pruebas[0].pk, empleado)
    assert estudio.pruebas_asignadas.filter(prueba=pruebas[0]).count() == 1


def test_estudio_no_modificable_rechaza_agregar(estudio, prueba_extra, empleado, monkeypatch):
    monkeypatch.setattr(Estudio, "admite_modificaciones", property(lambda self: False))
    with pytest.raises(GestionPruebasError, match="ya no admite cambios"):
        agregar_prueba(estudio.pk, prueba_extra.pk, empleado)
    assert codigos(estudio) == {"TEST-A", "TEST-B"}
