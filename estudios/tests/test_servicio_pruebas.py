import uuid

import pytest

from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Estudio, PruebaEstudio
from estudios.servicios import (
    GestionPruebasError,
    PruebaYaAsignada,
    agregar_prueba,
    crear_estudio,
)

pytestmark = pytest.mark.django_db


def codigos(estudio):
    return sorted(estudio.pruebas_asignadas.values_list("prueba__codigo", flat=True))


def capturar_estado(estudio, otro):
    estudio.refresh_from_db()
    tipo = estudio.tipo
    tipo.refresh_from_db()
    return {
        "cabecera": {
            campo: getattr(estudio, campo)
            for campo in (
                "muestra_id",
                "tipo_id",
                "estado",
                "creado_por_id",
                "fecha_creacion",
                "tipo_nombre_snapshot",
                "tipo_descripcion_snapshot",
                "tipo_version_snapshot",
            )
        },
        "tipo": (sorted(tipo.pruebas.values_list("pk", flat=True)), tipo.version),
        "otro": codigos(otro),
    }


def test_agregar_prueba_crea_asignacion(estudio, prueba_extra, empleado):
    asignacion = agregar_prueba(estudio.pk, prueba_extra.pk, empleado)
    assert asignacion.prueba == prueba_extra
    assert asignacion.estado == EstadoPruebaEstudio.PENDIENTE
    assert PruebaEstudio.objects.get(pk=asignacion.pk).estado == EstadoPruebaEstudio.PENDIENTE
    assert codigos(estudio) == ["TEST-A", "TEST-B", "TEST-C"]


def test_agregar_no_modifica_cabecera_tipo_ni_otros_estudios(
    estudio, datos, prueba_extra, empleado
):
    otro = crear_estudio({**datos, "clave": str(uuid.uuid4())}, empleado)
    antes = capturar_estado(estudio, otro)
    agregar_prueba(estudio.pk, prueba_extra.pk, empleado)
    assert capturar_estado(estudio, otro) == antes


def test_agregar_prueba_ya_asignada_rechazada(estudio, pruebas, empleado):
    with pytest.raises(PruebaYaAsignada, match="La prueba TEST-A ya forma parte del estudio."):
        agregar_prueba(estudio.pk, pruebas[0].pk, empleado)
    assert estudio.pruebas_asignadas.filter(prueba=pruebas[0]).count() == 1


@pytest.mark.parametrize(
    "estado",
    [EstadoEstudio.EN_PROCESO, EstadoEstudio.FINALIZADO, EstadoEstudio.INFORME_GENERADO],
)
def test_estudio_no_modificable_rechaza_agregar(estudio, prueba_extra, empleado, estado):
    Estudio.objects.filter(pk=estudio.pk).update(estado=estado)
    with pytest.raises(
        GestionPruebasError, match="Este estudio ya no admite cambios en sus pruebas."
    ):
        agregar_prueba(estudio.pk, prueba_extra.pk, empleado)
    assert codigos(estudio) == ["TEST-A", "TEST-B"]
