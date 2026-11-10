"""Reemplazo en cascada (SCRUM-73, US6)."""

import pytest

from estudios.models import TipoEstudio
from pruebas import gestion
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


@pytest.fixture
def escenario():
    ca = Prueba.objects.create(codigo="CA", nombre="Calcio", unidad="mg/l")
    ca2 = Prueba.objects.create(codigo="CA2", nombre="Calcio nuevo", unidad="mg/l")
    mg = Prueba.objects.create(
        codigo="MG",
        nombre="Magnesio",
        unidad="mg/l",
        tipo_calculo="FORMULA",
        formula="({CA}*2.5)*0.243",
        es_calculada=True,
    )
    otra_unidad = Prueba.objects.create(codigo="OTRA", nombre="Otra", unidad="ml")
    tipo = TipoEstudio.objects.create(nombre="Dureza")
    tipo.pruebas.set([ca, mg])
    con_las_dos = TipoEstudio.objects.create(nombre="Con las dos")
    con_las_dos.pruebas.set([ca, ca2])
    return {"ca": ca, "ca2": ca2, "mg": mg, "otra": otra_unidad, "tipo": tipo, "dos": con_las_dos}


def desactivar(usuario, prueba, reemplazo):
    prueba.refresh_from_db()
    return gestion.gestionar_prueba(
        usuario=usuario,
        operacion="desactivar",
        prueba_id=prueba.pk,
        version_esperada=prueba.version,
        reemplazo_id=reemplazo.pk if reemplazo else None,
    )


def test_candidatas(escenario):
    candidatas = {p.codigo for p in gestion.candidatas_reemplazo(escenario["ca"])}
    assert candidatas == {"CA2"}  # ni ella, ni MG (depende de CA), ni OTRA (otra unidad)


@pytest.mark.parametrize("clave", ["mg", "otra", "ca"])
def test_reemplazo_incompatible(administrador_catalogo, escenario, clave):
    with pytest.raises(gestion.DatosInvalidos):
        desactivar(administrador_catalogo, escenario["ca"], escenario[clave])
    escenario["ca"].refresh_from_db()
    assert escenario["ca"].activa and escenario["ca"].reemplazada_por is None


def test_cascada(administrador_catalogo, escenario):
    version_tipo = escenario["tipo"].version
    resultado = desactivar(administrador_catalogo, escenario["ca"], escenario["ca2"])
    assert (resultado.estado, resultado.reemplazo) == ("reemplazada", "CA2")
    ca, mg = (Prueba.objects.get(codigo=c) for c in ("CA", "MG"))
    assert not ca.activa and ca.reemplazada_por.codigo == "CA2"
    assert mg.formula == "({CA2}*2.5)*0.243" and mg.version == 2
    tipo = TipoEstudio.objects.get(pk=escenario["tipo"].pk)
    assert set(tipo.pruebas.values_list("codigo", flat=True)) == {"CA2", "MG"}
    assert tipo.version == version_tipo + 1
    dos = TipoEstudio.objects.get(pk=escenario["dos"].pk)
    assert list(dos.pruebas.values_list("codigo", flat=True)) == ["CA2"]


def test_cascada_atomica(administrador_catalogo, escenario, monkeypatch):
    def fallar(*args, **kwargs):
        raise RuntimeError("falla")

    monkeypatch.setattr(gestion, "_marcar", fallar)
    with pytest.raises(RuntimeError):
        desactivar(administrador_catalogo, escenario["ca"], escenario["ca2"])
    assert Prueba.objects.get(codigo="MG").formula == "({CA}*2.5)*0.243"
    assert Prueba.objects.get(codigo="CA").activa


def crear_reemplazo(usuario, prueba, datos):
    prueba.refresh_from_db()
    return gestion.gestionar_prueba(
        usuario=usuario,
        operacion="reemplazar",
        prueba_id=prueba.pk,
        version_esperada=prueba.version,
        datos=datos,
    )


def test_crear_y_reemplazar(administrador_catalogo, escenario, datos_prueba):
    resultado = crear_reemplazo(
        administrador_catalogo, escenario["ca"], datos_prueba(codigo="CA3", nombre="Calcio 3")
    )
    assert (resultado.estado, resultado.reemplazo) == ("creada_reemplazo", "CA3")
    ca3 = Prueba.objects.get(pk=resultado.prueba_id)
    assert ca3.activa and ca3.creada_por == administrador_catalogo
    ca = Prueba.objects.get(codigo="CA")
    assert not ca.activa and ca.reemplazada_por == ca3
    assert Prueba.objects.get(codigo="MG").formula == "({CA3}*2.5)*0.243"
    tipo = TipoEstudio.objects.get(pk=escenario["tipo"].pk)
    assert set(tipo.pruebas.values_list("codigo", flat=True)) == {"CA3", "MG"}


@pytest.mark.parametrize(
    ("cambios", "campo"),
    [
        ({"unidad": "ml"}, "unidad"),
        ({"tipo_calculo": "FORMULA", "formula": "{CA}*1"}, "formula"),
        ({"tipo_calculo": "FORMULA", "formula": "{MG}*1"}, "formula"),
        ({"codigo": "ca2"}, "codigo"),
    ],
)
def test_crear_y_reemplazar_rechaza(
    administrador_catalogo, escenario, datos_prueba, cambios, campo
):
    antes = Prueba.objects.count()
    with pytest.raises(gestion.DatosInvalidos) as error:
        crear_reemplazo(administrador_catalogo, escenario["ca"], datos_prueba(**cambios))
    assert campo in error.value.errores
    assert Prueba.objects.count() == antes
    assert Prueba.objects.get(codigo="CA").activa
