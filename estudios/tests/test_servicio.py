import uuid

import pytest
from django.db import DatabaseError

from estudios.models import Estudio, PruebaEstudio
from estudios.servicios import CrearEstudioError, VersionDesactualizada, crear_estudio

pytestmark = pytest.mark.django_db


def test_creacion_exacta(datos, empleado, tipo, muestra):
    e = crear_estudio(datos, empleado)
    assert e.muestra == muestra and e.tipo == tipo
    assert e.estado == "pendiente_analisis" and e.creado_por == empleado
    assert e.fecha_creacion and e.pk
    assert e.tipo_nombre_snapshot == tipo.nombre
    assert e.tipo_descripcion_snapshot == tipo.descripcion
    assert set(e.pruebas_asignadas.values_list("prueba_id", flat=True)) == set(
        tipo.pruebas.values_list("pk", flat=True)
    )


def test_reenvio_y_solicitud_deliberada(datos, empleado):
    a = crear_estudio(datos, empleado)
    assert crear_estudio(datos, empleado).pk == a.pk
    b = crear_estudio({**datos, "clave": str(uuid.uuid4())}, empleado)
    assert b.pk != a.pk and Estudio.objects.count() == 2


def test_cliente_inactivo(datos, empleado, cliente_a):
    cliente_a.activo = False
    cliente_a.save()
    crear_estudio(datos, empleado)
    cliente_a.refresh_from_db()
    assert not cliente_a.activo


def test_version_cambiada(datos, empleado, tipo, cambiar_tipo):
    cambiar_tipo(tipo, descripcion="Otro texto")
    with pytest.raises(VersionDesactualizada):
        crear_estudio(datos, empleado)
    assert not Estudio.objects.exists()


def test_reenvio_tras_desactivar(datos, empleado, tipo, cambiar_tipo):
    e = crear_estudio(datos, empleado)
    cambiar_tipo(tipo, activo=False, nombre="Otro nombre")
    assert crear_estudio(datos, empleado).pk == e.pk
    e.refresh_from_db()
    assert e.tipo_nombre_snapshot == "Tipo de test"


def test_uuid_otra_operacion(datos, empleado):
    crear_estudio(datos, empleado)
    with pytest.raises(CrearEstudioError):
        crear_estudio({**datos, "muestra": 999999}, empleado)
    assert Estudio.objects.count() == 1


def test_rollback(datos, empleado, monkeypatch):
    original = PruebaEstudio.objects.bulk_create

    def fallar(*args, **kwargs):
        original(*args, **kwargs)
        raise DatabaseError("falla de test")

    with monkeypatch.context() as m:
        m.setattr(PruebaEstudio.objects, "bulk_create", fallar)
        with pytest.raises(DatabaseError):
            crear_estudio(datos, empleado)
    assert Estudio.objects.count() == PruebaEstudio.objects.count() == 0
    assert crear_estudio(datos, empleado).pk


@pytest.mark.parametrize("caso", ["inactivo", "vacio", "inexistente", "muestra"])
def test_rechazos(datos, empleado, tipo, caso):
    if caso == "inactivo":
        tipo.activo = False
        tipo.save()
    elif caso == "vacio":
        tipo.pruebas.clear()
    elif caso == "inexistente":
        datos["tipo"] = 999999
    else:
        datos["muestra"] = 999999
    with pytest.raises(CrearEstudioError):
        crear_estudio(datos, empleado)
    assert not Estudio.objects.exists()


def test_otro_tipo_independiente(datos, empleado, tipo, pruebas):
    from estudios.models import TipoEstudio

    primero = crear_estudio(datos, empleado)
    otro = TipoEstudio.objects.create(nombre="Segundo tipo de test")
    otro.pruebas.set([pruebas[1]])
    segundo = crear_estudio(
        {**datos, "clave": str(uuid.uuid4()), "tipo": otro.pk, "version": otro.version},
        empleado,
    )
    assert primero.pk != segundo.pk and primero.muestra_id == segundo.muestra_id
    primero.refresh_from_db()
    assert primero.tipo_id == tipo.pk and primero.pruebas_asignadas.count() == 2
    assert segundo.pruebas_asignadas.count() == 1


@pytest.mark.parametrize("cambio", ["tipo", "usuario"])
def test_uuid_no_reutilizable(datos, empleado, django_user_model, cambio):
    e = crear_estudio(datos, empleado)
    usuario = empleado
    if cambio == "tipo":
        datos = {**datos, "tipo": 999999}
    else:
        usuario = django_user_model.objects.create_user(
            email="ajeno@ejemplo.com",
            password="Clave-Valida-123",
            is_active=True,
        )
    with pytest.raises(CrearEstudioError):
        crear_estudio(datos, usuario)
    assert Estudio.objects.get().pk == e.pk
