from hashlib import sha256

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.utils import timezone

from informes.models import BorradorConclusion

pytestmark = pytest.mark.django_db


@pytest.fixture
def borrador(estudio_de, bioquimico):
    return BorradorConclusion.objects.create(
        estudio=estudio_de("PH"),
        editado_por=bioquimico,
        fecha_edicion=timezone.now(),
        huella_hechos="a" * 64,
        origen_propuesta="manual",
    )


def test_defaults_y_sin_permisos_nuevos(borrador):
    assert borrador.revision == 1
    assert borrador.texto_editorial == borrador.texto_final == ""
    assert borrador.hechos == {}
    assert borrador.advertencias == []
    assert not borrador.requiere_revision
    assert borrador.solicitud_propuesta is None
    assert borrador.aprobada_por_id is None
    assert borrador.nombre_aprobador == ""
    assert borrador.huella_texto_aprobado == ""
    assert borrador.huella_hechos_aprobados == ""
    assert BorradorConclusion._meta.default_permissions == ()
    assert not Permission.objects.filter(content_type__model="borradorconclusion").exists()
    borrador.full_clean()


def test_un_borrador_por_estudio(borrador):
    with pytest.raises(IntegrityError), transaction.atomic():
        BorradorConclusion.objects.create(
            estudio=borrador.estudio,
            editado_por=borrador.editado_por,
            fecha_edicion=timezone.now(),
            huella_hechos="a" * 64,
            origen_propuesta="manual",
        )


@pytest.mark.parametrize("campo,valor", [("revision", 0), ("nombre_aprobador", "Parcial")])
def test_constraints_incompletos(borrador, campo, valor):
    with pytest.raises(IntegrityError), transaction.atomic():
        BorradorConclusion.objects.filter(pk=borrador.pk).update(**{campo: valor})


def aprobar_fila(borrador):
    borrador.texto_editorial = borrador.texto_final = "Texto aprobado"
    borrador.aprobada_por = borrador.editado_por
    borrador.nombre_aprobador = "Profesional sintético"
    borrador.fecha_aprobacion = timezone.now()
    borrador.revision_aprobada = borrador.revision
    borrador.huella_texto_aprobado = sha256(borrador.texto_final.encode()).hexdigest()
    borrador.huella_hechos_aprobados = borrador.huella_hechos


def test_aprobacion_completa_valida(borrador):
    aprobar_fila(borrador)
    borrador.full_clean()
    borrador.save()
    borrador.refresh_from_db()
    assert borrador.aprobada_por == borrador.editado_por


AUSENCIAS = {
    "aprobada_por_id": None,
    "fecha_aprobacion": None,
    "revision_aprobada": None,
    "nombre_aprobador": "",
    "huella_texto_aprobado": "",
    "huella_hechos_aprobados": "",
}


@pytest.mark.parametrize("campo", AUSENCIAS)
def test_no_puede_completar_un_solo_campo(borrador, campo):
    aprobar_fila(borrador)
    valor = getattr(borrador, campo)
    with pytest.raises(IntegrityError), transaction.atomic():
        BorradorConclusion.objects.filter(pk=borrador.pk).update(**{campo: valor})


@pytest.mark.parametrize("campo,ausente", AUSENCIAS.items())
def test_no_puede_vaciar_un_campo_aprobado(borrador, campo, ausente):
    aprobar_fila(borrador)
    borrador.save()
    with pytest.raises(IntegrityError), transaction.atomic():
        BorradorConclusion.objects.filter(pk=borrador.pk).update(**{campo: ausente})


@pytest.mark.parametrize(
    "cambio",
    [
        {"revision_aprobada": 3},
        {"huella_hechos_aprobados": "b" * 64},
        {"requiere_revision": True},
        {"fecha_aprobacion": None},
    ],
)
def test_aprobacion_incoherente_rechazada_en_bd(borrador, cambio):
    aprobar_fila(borrador)
    borrador.save()
    with pytest.raises(IntegrityError), transaction.atomic():
        BorradorConclusion.objects.filter(pk=borrador.pk).update(**cambio)


@pytest.mark.parametrize(
    "cambio",
    [
        {"huella_hechos": "X" * 64},
        {"origen_propuesta": "otro"},
        {"motivo_respaldo": "secreto"},
        {"hechos": {"numero": 1.5}},
        {"texto_editorial": "invalido\x00"},
    ],
)
def test_validacion_de_campos(borrador, cambio):
    for campo, valor in cambio.items():
        setattr(borrador, campo, valor)
    with pytest.raises(ValidationError):
        borrador.full_clean()


def test_relaciones_protegidas(borrador):
    with pytest.raises(ProtectedError):
        borrador.editado_por.delete()
    with pytest.raises(ProtectedError):
        borrador.estudio.delete()


@pytest.mark.django_db(transaction=True)
def test_migracion_reversible_no_toca_informe(estudio_de, bioquimico):
    from estudios.tests.utiles import cargar, validar
    from informes.models import Informe
    from informes.servicios import emitir_informe

    estudio = estudio_de("PH")
    cargar(estudio, bioquimico, PH="7.4")
    validar(estudio, bioquimico, "PH")
    informe = emitir_informe(estudio.pk, bioquimico)
    contenido = informe.contenido
    try:
        MigrationExecutor(connection).migrate([("informes", "0005_envioinforme")])
        assert "informes_borradorconclusion" not in connection.introspection.table_names()
        assert Informe.objects.get(pk=informe.pk).contenido == contenido
    finally:
        MigrationExecutor(connection).migrate([("informes", "0006_borradorconclusion")])
    assert "informes_borradorconclusion" in connection.introspection.table_names()
    assert Informe.objects.get(pk=informe.pk).contenido == contenido
