import pytest

from estudios.catalogo import CatalogoNoDisponible, leer_configuracion
from estudios.models import TipoEstudio
from estudios.servicios import crear_estudio

pytestmark = pytest.mark.django_db


def test_lectura_completa(tipo, pruebas):
    c = leer_configuracion(tipo.pk)
    assert c["version"] == 1 and c["descripcion"] == "Descripción test"
    assert [p["id"] for p in c["pruebas"]] == [p.pk for p in pruebas]


@pytest.mark.parametrize("cambio", ["nombre", "descripcion", "activo", "pruebas"])
def test_snapshots_historicos(datos, empleado, tipo, pruebas, cambiar_tipo, cambio):
    e = crear_estudio(datos, empleado)
    valores = {"nombre": "Otro", "descripcion": "", "activo": False, "pruebas": [pruebas[0].pk]}
    t = cambiar_tipo(tipo, **{cambio: valores[cambio]})
    assert t.version == 2
    e.refresh_from_db()
    assert e.tipo_nombre_snapshot == "Tipo de test"
    assert e.tipo_descripcion_snapshot == "Descripción test"
    assert e.tipo_version_snapshot == 1
    assert e.pruebas_asignadas.count() == 2


def test_descripcion_vacia_historica(datos, empleado, tipo, cambiar_tipo):
    tipo.descripcion = ""
    tipo.save()
    e = crear_estudio(datos, empleado)
    cambiar_tipo(tipo, descripcion="Posterior")
    e.refresh_from_db()
    assert e.tipo_descripcion_snapshot == ""


def test_version_noop_y_rollback(tipo, cambiar_tipo):
    assert cambiar_tipo(tipo, nombre=tipo.nombre).version == 1
    from django.db import transaction

    with pytest.raises(RuntimeError), transaction.atomic():
        cambiar_tipo(tipo, descripcion="Descartado")
        raise RuntimeError("rollback")
    tipo.refresh_from_db()
    assert tipo.version == 1 and tipo.descripcion == "Descripción test"


def test_tipo_inexistente_o_no_disponible(tipo):
    with pytest.raises(CatalogoNoDisponible):
        leer_configuracion(999999)
    TipoEstudio.objects.filter(pk=tipo.pk).update(activo=False)
    with pytest.raises(CatalogoNoDisponible):
        leer_configuracion(tipo.pk)
