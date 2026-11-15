"""US 6.6 – US1: el catálogo ofrece «Curva de calibración» (specs/037-curva-calibracion)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse

from pruebas import gestion
from pruebas.formularios import PruebaForm
from pruebas.models import CurvaCalibracion, Prueba, PuntoCurva, TipoCalculo
from pruebas.tests.test_importacion import fila_prueba, importar_filas

pytestmark = pytest.mark.django_db


def crear(usuario, datos):
    resultado = gestion.gestionar_prueba(usuario=usuario, operacion="crear", datos=datos)
    return Prueba.objects.get(pk=resultado.prueba_id)


def editar(usuario, prueba, datos):
    prueba.refresh_from_db()
    return gestion.gestionar_prueba(
        usuario=usuario,
        operacion="editar",
        prueba_id=prueba.pk,
        version_esperada=prueba.version,
        datos=datos,
    )


def datos_curva(datos_prueba, **cambios):
    base = {
        "codigo": "NO2-C",
        "nombre": "Nitritos (curva)",
        "tipo_calculo": "CURVA",
        "unidad_medicion": "",
        "unidad": "mg/l",
    }
    return datos_prueba(**{**base, **cambios})


# Esc. 1 — tres opciones


def test_prueba_por_curva_opcion():
    opciones = dict(PruebaForm().fields["tipo_calculo"].choices)
    assert opciones == {
        "DIRECTO": "Directo",
        "FORMULA": "Fórmula",
        "CURVA": "Curva de calibración",
    }


# Esc. 2 — unidad obligatoria, sin fórmula, «Abs»


def test_prueba_por_curva_reglas(administrador_catalogo, datos_prueba):
    prueba = crear(administrador_catalogo, datos_curva(datos_prueba, formula="x*2"))
    assert prueba.tipo_calculo == TipoCalculo.CURVA
    assert prueba.formula == ""  # se descarta, como con Directo
    assert prueba.unidad_medicion == "Abs"
    assert prueba.es_calculada is False

    form = PruebaForm(data=datos_curva(datos_prueba, codigo="NO2-B", unidad=""))
    assert not form.is_valid()
    assert form.errors["unidad"] == ["Indicá la unidad del resultado (la de la concentración)."]

    con_unidad_propia = crear(
        administrador_catalogo, datos_curva(datos_prueba, codigo="NO2-D", unidad_medicion="UA")
    )
    assert con_unidad_propia.unidad_medicion == "UA"


def test_prueba_por_curva_reglas_del_modelo():
    prueba = Prueba(codigo="C1", nombre="C", tipo_calculo=TipoCalculo.CURVA, formula="x*2")
    with pytest.raises(ValidationError) as error:
        prueba.full_clean()
    assert "Una prueba por curva de calibración no lleva fórmula." in str(error.value)
    sin_unidad = Prueba(codigo="C2", nombre="C", tipo_calculo=TipoCalculo.CURVA)
    with pytest.raises(ValidationError) as error:
        sin_unidad.full_clean()
    assert "Indicá la unidad del resultado" in str(error.value)
    with pytest.raises(IntegrityError), transaction.atomic():
        Prueba.objects.create(
            codigo="C3", nombre="C", tipo_calculo=TipoCalculo.CURVA, unidad="mg/l", formula="x"
        )


# Esc. 3 — ficha


def test_prueba_por_curva_ficha(cliente_catalogo, prueba_curva):
    html = cliente_catalogo.get(reverse("catalogo:ficha", args=[prueba_curva.pk])).content.decode()
    assert "Curvas de calibración" in html
    assert "Sin curva vigente" in html
    assert "Nueva curva" in html


def test_ficha_muestra_la_vigente(cliente_catalogo, prueba_curva, curva_de):
    curva_de(prueba_curva, r2="0.9996025692", pendiente="0.499", ordenada="0.0012")
    html = cliente_catalogo.get(reverse("catalogo:ficha", args=[prueba_curva.pk])).content.decode()
    assert "Sin curva vigente" not in html
    assert "0,9996" in html


def test_ficha_sin_curvas_si_no_es_por_curva(cliente_catalogo, prueba_libre):
    html = cliente_catalogo.get(reverse("catalogo:ficha", args=[prueba_libre.pk])).content.decode()
    assert "Curvas de calibración" not in html


# Esc. 4 — una prueba en uso no pasa a Curva


def test_en_uso_no_pasa_a_curva(administrador_catalogo, prueba_en_estudio, datos_prueba):
    datos = gestion.datos_de(prueba_en_estudio)
    datos.update(tipo_calculo="CURVA", unidad="mg/l")
    with pytest.raises(gestion.PruebaEnUso) as error:
        editar(administrador_catalogo, prueba_en_estudio, datos)
    assert str(error.value) == gestion.MENSAJE_EN_USO
    prueba_en_estudio.refresh_from_db()
    assert prueba_en_estudio.tipo_calculo == TipoCalculo.DIRECTO


# R12 — curvas cargadas y cambio de tipo; eliminar


def test_cambio_tipo_con_curvas(administrador_catalogo, prueba_curva, curva_de):
    curva_de(prueba_curva)
    datos = gestion.datos_de(prueba_curva)
    datos["tipo_calculo"] = "DIRECTO"
    with pytest.raises(gestion.DatosInvalidos) as error:
        editar(administrador_catalogo, prueba_curva, datos)
    assert error.value.errores == {
        "tipo_calculo": "Tiene curvas de calibración cargadas: borralas antes de cambiar el tipo "
        "de cálculo."
    }
    prueba_curva.refresh_from_db()
    assert prueba_curva.tipo_calculo == TipoCalculo.CURVA


def test_cambio_tipo_sin_curvas(administrador_catalogo, prueba_curva):
    datos = gestion.datos_de(prueba_curva)
    datos["tipo_calculo"] = "DIRECTO"
    editar(administrador_catalogo, prueba_curva, datos)
    prueba_curva.refresh_from_db()
    assert prueba_curva.tipo_calculo == TipoCalculo.DIRECTO


def test_eliminar_borra_curvas(administrador_catalogo, prueba_curva, curva_de):
    curva_de(prueba_curva, vigente=False)
    curva_de(prueba_curva)
    gestion.gestionar_prueba(
        usuario=administrador_catalogo,
        operacion="eliminar",
        prueba_id=prueba_curva.pk,
        version_esperada=prueba_curva.version,
    )
    assert not Prueba.objects.filter(pk=prueba_curva.pk).exists()
    assert not CurvaCalibracion.objects.exists()
    assert not PuntoCurva.objects.exists()


# R13 — la importación del catálogo acepta el tipo


def test_importacion_acepta_curva(tmp_path):
    importar_filas(tmp_path, [fila_prueba(codigo="NO2-C", tipo_calculo="CURVA", unidad="mg/l")])
    prueba = Prueba.objects.get(codigo="NO2-C")
    assert prueba.tipo_calculo == TipoCalculo.CURVA
    assert prueba.curva_vigente is None


def test_en_uso_sin_unidad_de_medicion_edita_limites(
    administrador_catalogo, muestra, empleado, estudio_de
):
    """Una prueba por curva importada sin unidad de medición y ya en uso: «Abs» no se completa
    (sería un cambio del método) y se pueden editar sus límites."""
    prueba = Prueba.objects.create(
        codigo="NO2-I", nombre="Importada", tipo_calculo=TipoCalculo.CURVA, unidad="mg/l"
    )
    estudio_de("NO2-I")
    datos = gestion.datos_de(prueba)
    datos["limite_max"] = "3"
    editar(administrador_catalogo, prueba, datos)
    prueba.refresh_from_db()
    assert prueba.limite_max == "3"
    assert prueba.unidad_medicion == ""
