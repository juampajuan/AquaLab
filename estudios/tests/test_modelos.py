import uuid

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from estudios.models import TipoEstudio, TipoEstudioPrueba

pytestmark = pytest.mark.django_db


def test_nombre_tipo_unico(tipo):
    otro = TipoEstudio(nombre="  TIPO DE TEST ")
    with pytest.raises(ValidationError):
        otro.full_clean()
    with pytest.raises(IntegrityError), transaction.atomic():
        TipoEstudio.objects.create(nombre="TIPO DE TEST")


def test_descripcion_opcional_y_nombres_distintos():
    for nombre in ["Canal", "Cánal", "Ca nal", "Ca  nal"]:
        t = TipoEstudio(nombre=nombre)
        t.full_clean()
        t.save()
        assert t.descripcion == "" and t.version == 1


def test_version_positiva(tipo):
    with pytest.raises(IntegrityError), transaction.atomic():
        TipoEstudio.objects.filter(pk=tipo.pk).update(version=0)


def test_asociacion_tipo_unica_y_protegida(tipo, pruebas):
    with pytest.raises(IntegrityError), transaction.atomic():
        TipoEstudioPrueba.objects.create(tipo=tipo, prueba=pruebas[0])
    with pytest.raises(ProtectedError):
        pruebas[0].delete()


def test_modelos_estudio(datos, empleado, tipo, muestra):
    from estudios.models import Estudio, PruebaEstudio
    from estudios.servicios import crear_estudio

    e = crear_estudio(datos, empleado)
    with pytest.raises(IntegrityError), transaction.atomic():
        PruebaEstudio.objects.create(estudio=e, prueba=tipo.pruebas.first())
    with pytest.raises(ProtectedError):
        muestra.delete()
    with pytest.raises(ProtectedError):
        tipo.delete()
    with pytest.raises(IntegrityError), transaction.atomic():
        Estudio.objects.create(
            muestra=muestra,
            tipo=tipo,
            creado_por=empleado,
            tipo_nombre_snapshot="Test",
            tipo_version_snapshot=1,
            clave_idempotencia=uuid.UUID(datos["clave"]),
        )


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("tipo_nombre_snapshot", "x" * 151),
        ("tipo_version_snapshot", 0),
    ],
)
def test_validaciones_estudio(datos, empleado, campo, valor):
    from estudios.servicios import crear_estudio

    e = crear_estudio(datos, empleado)
    e.full_clean()
    setattr(e, campo, valor)
    with pytest.raises(ValidationError):
        e.full_clean()


def test_uuid_obligatorio_y_identificador_propio(muestra, tipo, empleado):
    from estudios.models import Estudio, PruebaEstudio
    from estudios.servicios import crear_estudio

    with pytest.raises(IntegrityError), transaction.atomic():
        Estudio.objects.create(
            muestra=muestra,
            tipo=tipo,
            creado_por=empleado,
            tipo_nombre_snapshot=tipo.nombre,
            tipo_version_snapshot=1,
        )
    datos = {
        "clave": str(uuid.uuid4()),
        "muestra": muestra.pk,
        "tipo": tipo.pk,
        "version": tipo.version,
    }
    e = crear_estudio(datos, empleado)
    assert e.pk != muestra.numero_pi
    campo = Estudio._meta.get_field("estado")
    assert not campo.editable
    assert list(campo.choices) == [
        ("pendiente_analisis", "Pendiente de análisis"),
        ("en_proceso", "En proceso"),
        ("finalizado", "Finalizado"),
        ("informe_generado", "Informe generado"),
    ]
    assert not Estudio._meta.get_field("clave_idempotencia").null
    campo_prueba = PruebaEstudio._meta.get_field("estado")
    assert not campo_prueba.editable
    assert campo_prueba.default == "pendiente"
    assert list(campo_prueba.choices) == [
        ("pendiente", "Pendiente"),
        ("cargada", "Cargada"),
        ("completada", "Completada"),
    ]
    assert list(e.pruebas_asignadas.values_list("estado", flat=True)) == ["pendiente", "pendiente"]


def test_admite_modificaciones_solo_pendiente_analisis(estudio):
    from estudios.models import EstadoEstudio

    assert estudio.admite_modificaciones
    for estado in EstadoEstudio.values:
        estudio.estado = estado
        assert estudio.admite_modificaciones == (estado == EstadoEstudio.PENDIENTE_ANALISIS)


def test_puede_quitarse_solo_pendiente(asignacion):
    from estudios.models import EstadoPruebaEstudio

    assert asignacion.puede_quitarse()
    for estado in (EstadoPruebaEstudio.CARGADA, EstadoPruebaEstudio.COMPLETADA):
        asignacion.estado = estado
        assert not asignacion.puede_quitarse()
