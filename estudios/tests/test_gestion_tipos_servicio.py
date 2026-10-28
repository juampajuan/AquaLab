import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import DatabaseError, connection
from django.test.utils import CaptureQueriesContext

from estudios.catalogo import CatalogoNoDisponible, leer_configuracion
from estudios.gestion_tipos import (
    DatosTipoInvalidos,
    FalloPersistencia,
    NoAutorizado,
    TipoNoExiste,
    TipoUtilizado,
    VersionTipoDesactualizada,
    gestionar_tipo_estudio,
    leer_tipo_administrativo,
)
from estudios.models import EstadoEstudio, TipoEstudio
from estudios.servicios import VersionDesactualizada, crear_estudio
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


def test_lector_incluye_inactivos_y_vacios(gestor, tipo_inactivo):
    tipo_inactivo.pruebas.clear()
    config = leer_tipo_administrativo(usuario=gestor, tipo_id=tipo_inactivo.pk)
    assert config["activo"] is False
    assert config["pruebas"] == []
    with pytest.raises(CatalogoNoDisponible):
        leer_configuracion(tipo_inactivo.pk)


@pytest.mark.parametrize("cuenta", ["anonimo", "empleado", "staff_sin_permiso"])
def test_permiso_antes_de_lectura(cuenta, request, django_assert_num_queries):
    usuario = AnonymousUser() if cuenta == "anonimo" else request.getfixturevalue(cuenta)
    if cuenta != "anonimo":
        usuario.has_perm("estudios.gestionar_catalogo")
    with django_assert_num_queries(0), pytest.raises(NoAutorizado):
        leer_tipo_administrativo(usuario=usuario, tipo_id=99999)


def alta(gestor, pruebas, **cambios):
    datos = {
        "nombre": "  DEMO Alta  ",
        "descripcion": "  descripción  ",
        "prueba_ids": [p.pk for p in pruebas],
    }
    return gestionar_tipo_estudio(usuario=gestor, operacion="crear", datos={**datos, **cambios})


def test_alta_exacta_y_reenvio(gestor, pruebas):
    cantidad = Prueba.objects.count()
    resultado = alta(gestor, pruebas, prueba_ids=[pruebas[0].pk] * 2)
    tipo = TipoEstudio.objects.get(pk=resultado.tipo_id)
    assert (tipo.nombre, tipo.descripcion, tipo.activo, tipo.version) == (
        "DEMO Alta",
        "  descripción  ",
        True,
        1,
    )
    assert list(tipo.pruebas.all()) == [pruebas[0]]
    assert resultado.estado == "creado"
    assert Prueba.objects.count() == cantidad
    with pytest.raises(DatosTipoInvalidos):
        alta(gestor, pruebas, nombre="demo ALTA")


@pytest.mark.parametrize(
    "datos",
    [
        {"nombre": " "},
        {"nombre": "x" * 151},
        {"prueba_ids": []},
        {"prueba_ids": [999999]},
        {"prueba_ids": [True]},
        {"prueba_ids": "1"},
        {"nombre": None},
        {"descripcion": []},
    ],
)
def test_alta_invalida_no_guarda(gestor, pruebas, datos):
    with pytest.raises(DatosTipoInvalidos):
        alta(gestor, pruebas, **datos)
    assert not TipoEstudio.objects.exists()


def test_unicidad_tildes_espacios_y_descripcion_vacia(gestor, pruebas):
    for nombre in ["Analisis", "Análisis", "Aná lisis", "Aná  lisis"]:
        alta(gestor, pruebas, nombre=nombre, descripcion="")
    assert TipoEstudio.objects.count() == 4
    assert not TipoEstudio.objects.exclude(descripcion="").exists()


@pytest.mark.parametrize("despues", [False, True])
def test_alta_rollback(gestor, pruebas, despues):
    # El método real escribe antes de fallar para acreditar rollback de cabecera y composición.
    from estudios.models import TipoEstudio

    manager = TipoEstudio.pruebas.related_manager_cls
    original = manager.set

    def fallar(self, *args, **kwargs):
        if despues:
            original(self, *args, **kwargs)
        raise DatabaseError("fallo controlado")

    with patch.object(manager, "set", fallar), pytest.raises(FalloPersistencia):
        alta(gestor, pruebas)
    assert not TipoEstudio.objects.exists()


def editar(gestor, tipo, **cambios):
    datos = {
        "nombre": tipo.nombre,
        "descripcion": tipo.descripcion,
        "prueba_ids": list(tipo.pruebas.values_list("pk", flat=True)),
    }
    version = cambios.pop("version_esperada", tipo.version)
    return gestionar_tipo_estudio(
        usuario=gestor,
        operacion="editar",
        tipo_id=tipo.pk,
        version_esperada=version,
        datos={**datos, **cambios},
    )


def test_noop_sin_dml_y_stale_no_se_acepta(gestor, tipo):
    ids = list(tipo.pruebas.values_list("pk", flat=True))
    with CaptureQueriesContext(connection) as queries:
        resultado = editar(
            gestor, tipo, nombre="  " + tipo.nombre + "  ", prueba_ids=ids[::-1] + ids
        )
    assert resultado.estado == "sin_cambios"
    assert not any(
        q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for q in queries
    )
    editar(gestor, tipo, nombre=tipo.nombre.upper())
    tipo.refresh_from_db()
    assert tipo.version == 2
    with pytest.raises(VersionTipoDesactualizada) as error:
        editar(gestor, tipo, version_esperada=1)
    assert error.value.configuracion["version"] == 2


@pytest.mark.parametrize("descripcion", ["", "Historia original"])
def test_historial_y_estudio_futuro(gestor, empleado, tipo, datos, descripcion):
    tipo.descripcion = descripcion
    tipo.save()
    anterior = crear_estudio(datos, empleado)
    snapshot = (
        anterior.tipo_nombre_snapshot,
        anterior.tipo_descripcion_snapshot,
        anterior.creado_por_id,
        anterior.fecha_creacion,
    )
    asignadas = list(anterior.pruebas_asignadas.values_list("prueba_id", flat=True))
    resultado = editar(
        gestor, tipo, nombre="Nuevo tipo", descripcion=" Nueva ", prueba_ids=asignadas[:1]
    )
    anterior.refresh_from_db()
    assert snapshot == (
        anterior.tipo_nombre_snapshot,
        anterior.tipo_descripcion_snapshot,
        anterior.creado_por_id,
        anterior.fecha_creacion,
    )
    assert list(anterior.pruebas_asignadas.values_list("prueba_id", flat=True)) == asignadas
    assert resultado.version_final == 2
    with pytest.raises(VersionDesactualizada):
        crear_estudio({**datos, "clave": str(uuid.uuid4())}, empleado)
    futuro = crear_estudio({**datos, "clave": str(uuid.uuid4()), "version": 2}, empleado)
    assert (futuro.tipo_nombre_snapshot, futuro.tipo_descripcion_snapshot) == (
        "Nuevo tipo",
        " Nueva ",
    )
    assert list(futuro.pruebas_asignadas.values_list("prueba_id", flat=True)) == asignadas[:1]


def test_editar_inactivo_y_no_quitar_ultima(gestor, tipo_inactivo):
    with pytest.raises(DatosTipoInvalidos):
        editar(gestor, tipo_inactivo, prueba_ids=[])
    editar(gestor, tipo_inactivo, descripcion="")
    tipo_inactivo.refresh_from_db()
    assert not tipo_inactivo.activo
    assert tipo_inactivo.version == 2


@pytest.mark.parametrize("despues", [False, True])
def test_edicion_rollback(gestor, tipo, despues):
    ids = list(tipo.pruebas.values_list("pk", flat=True))
    manager = TipoEstudio.pruebas.related_manager_cls
    original = manager.set

    def fallar(self, *args, **kwargs):
        if despues:
            original(self, *args, **kwargs)
        raise DatabaseError("fallo controlado")

    with patch.object(manager, "set", fallar), pytest.raises(FalloPersistencia):
        editar(gestor, tipo, nombre="No persistir", prueba_ids=ids[:1])
    tipo.refresh_from_db()
    assert tipo.nombre == "Tipo de test"
    assert tipo.version == 1
    assert list(tipo.pruebas.values_list("pk", flat=True)) == ids


def operar(gestor, tipo, operacion, version=None):
    return gestionar_tipo_estudio(
        usuario=gestor,
        operacion=operacion,
        tipo_id=tipo.pk,
        version_esperada=version or tipo.version,
    )


def test_disponibilidad_version_y_noop(gestor, tipo):
    assert operar(gestor, tipo, "desactivar").estado == "desactivado"
    tipo.refresh_from_db()
    assert not tipo.activo and tipo.version == 2
    with pytest.raises(VersionTipoDesactualizada):
        operar(gestor, tipo, "reactivar", version=1)
    with CaptureQueriesContext(connection) as queries:
        assert operar(gestor, tipo, "desactivar").estado == "sin_cambios"
    assert not any(q["sql"].startswith(("UPDATE", "INSERT", "DELETE")) for q in queries)
    assert operar(gestor, tipo, "reactivar").estado == "reactivado"
    tipo.refresh_from_db()
    assert tipo.activo and tipo.version == 3
    assert operar(gestor, tipo, "reactivar").estado == "sin_cambios"


def test_legado_vacio_no_reactiva_pero_se_retira(gestor, tipo):
    tipo.pruebas.clear()
    operar(gestor, tipo, "desactivar")
    tipo.refresh_from_db()
    with pytest.raises(DatosTipoInvalidos):
        operar(gestor, tipo, "reactivar")
    assert operar(gestor, tipo, "eliminar").version_final is None
    assert not TipoEstudio.objects.exists()
    assert Prueba.objects.count() == 2
    with pytest.raises(TipoNoExiste):
        operar(gestor, tipo, "eliminar")


@pytest.mark.parametrize("estado", EstadoEstudio.values)
def test_proteccion_cualquier_historia(gestor, tipo, datos, empleado, estado):
    estudio = crear_estudio(datos, empleado)
    estudio.estado = estado
    estudio.save(update_fields=["estado"])
    operar(gestor, tipo, "desactivar")
    tipo.refresh_from_db()
    with pytest.raises(TipoUtilizado):
        operar(gestor, tipo, "eliminar")
    estudio.refresh_from_db()
    assert estudio.tipo_id == tipo.pk
    assert estudio.pruebas_asignadas.count() == 2
    assert estudio.tipo_nombre_snapshot == "Tipo de test"


@pytest.mark.parametrize("operacion", ["crear", "editar", "desactivar", "reactivar", "eliminar"])
def test_servicio_sin_permiso_rechaza(empleado, operacion):
    with pytest.raises(NoAutorizado):
        gestionar_tipo_estudio(
            usuario=empleado, operacion=operacion, tipo_id=999, version_esperada=1
        )


def test_eliminar_rollback(gestor, tipo):
    original = TipoEstudio.delete

    def fallar(self, *args, **kwargs):
        original(self, *args, **kwargs)
        raise DatabaseError("fallo después de eliminar")

    pk = tipo.pk
    with patch.object(TipoEstudio, "delete", fallar), pytest.raises(FalloPersistencia):
        operar(gestor, tipo, "eliminar")
    tipo = TipoEstudio.objects.get(pk=pk)
    assert tipo.pruebas.count() == 2
    assert tipo.version == 1


def test_edicion_unicidad_y_referencias_invalidas(gestor, tipo):
    otro = TipoEstudio.objects.create(nombre="Reservado")
    for cambios in [{"nombre": " RESERVADO "}, {"prueba_ids": [999999]}, {"nombre": " "}]:
        with pytest.raises(DatosTipoInvalidos):
            editar(gestor, tipo, **cambios)
        tipo.refresh_from_db()
        assert tipo.version == 1 and tipo.nombre == "Tipo de test"
    assert otro.nombre == "Reservado"


@pytest.mark.parametrize("operacion,activo", [("desactivar", True), ("reactivar", False)])
def test_disponibilidad_rollback_y_sin_historia_alterada(
    gestor, tipo, datos, empleado, operacion, activo
):
    estudio = crear_estudio(datos, empleado)
    tipo.activo = activo
    tipo.save()
    original = TipoEstudio.save

    def fallar(self, *args, **kwargs):
        original(self, *args, **kwargs)
        raise DatabaseError("fallo tras escribir disponibilidad")

    with patch.object(TipoEstudio, "save", fallar), pytest.raises(FalloPersistencia):
        operar(gestor, tipo, operacion)
    tipo.refresh_from_db()
    assert tipo.activo == activo and tipo.version == 1
    assert estudio.pruebas_asignadas.count() == 2
    assert estudio.tipo_nombre_snapshot == "Tipo de test"


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("tipo_id", True),
        ("tipo_id", 1.5),
        ("tipo_id", -1),
        ("version_esperada", 0),
        ("version_esperada", "x"),
    ],
)
def test_entrada_invalida_controlada(gestor, tipo, campo, valor):
    args = {"usuario": gestor, "operacion": "eliminar", "tipo_id": tipo.pk, "version_esperada": 1}
    with pytest.raises(DatosTipoInvalidos):
        gestionar_tipo_estudio(**{**args, campo: valor})
    assert TipoEstudio.objects.filter(pk=tipo.pk).exists()


def test_usuario_inactivo_rechazado_en_servicio(gestor, tipo):
    gestor.is_active = False
    gestor.save(update_fields=["is_active"])
    with pytest.raises(NoAutorizado):
        operar(gestor, tipo, "desactivar")
    tipo.refresh_from_db()
    assert tipo.activo and tipo.version == 1


def test_reactivado_disponible_y_revision_anterior_rechazada(
    gestor, tipo_inactivo, datos, empleado
):
    operar(gestor, tipo_inactivo, "reactivar")
    assert leer_configuracion(tipo_inactivo.pk)["version"] == 2
    with pytest.raises(VersionDesactualizada):
        crear_estudio(datos, empleado)
    estudio = crear_estudio({**datos, "version": 2}, empleado)
    assert estudio.pruebas_asignadas.count() == 2
