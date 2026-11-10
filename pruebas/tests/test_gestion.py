"""Servicio de gestión del catálogo (SCRUM-73): `pruebas/gestion.py`."""

import pytest

from estudios.models import Validacion
from estudios.tests.utiles import cargar, validar
from informes.models import Informe
from informes.servicios import emitir_informe
from pruebas import gestion
from pruebas.models import LimiteVertido, Prueba

pytestmark = pytest.mark.django_db


def crear(usuario, datos):
    resultado = gestion.gestionar_prueba(usuario=usuario, operacion="crear", datos=datos)
    return Prueba.objects.get(pk=resultado.prueba_id)


def operar(usuario, prueba, operacion, datos=None, **extra):
    prueba.refresh_from_db()
    return gestion.gestionar_prueba(
        usuario=usuario,
        operacion=operacion,
        prueba_id=prueba.pk,
        version_esperada=prueba.version,
        datos=datos or {},
        **extra,
    )


# --- Base ------------------------------------------------------------------------------------


def test_dependientes(administrador_catalogo, datos_prueba):
    base = crear(administrador_catalogo, datos_prueba())
    crear(
        administrador_catalogo,
        datos_prueba(codigo="TEST-FOR", tipo_calculo="FORMULA", formula="{TEST-DIR}*2"),
    )
    assert [p.codigo for p in gestion.dependientes(base)] == ["TEST-FOR"]


def test_version_desactualizada(administrador_catalogo, datos_prueba):
    prueba = crear(administrador_catalogo, datos_prueba())
    with pytest.raises(gestion.VersionDesactualizada):
        gestion.gestionar_prueba(
            usuario=administrador_catalogo,
            operacion="editar",
            prueba_id=prueba.pk,
            version_esperada=prueba.version + 1,
            datos=datos_prueba(nombre="Otro"),
        )


# --- US1: alta -------------------------------------------------------------------------------


def test_alta_directa_y_formula(administrador_catalogo, datos_prueba):
    directa = crear(
        administrador_catalogo,
        datos_prueba(cloacal_limite_max="20", cloacal_norma="AGOSBA", formula="ignorada"),
    )
    assert directa.activa and directa.version == 1 and directa.formula == ""
    assert directa.creada_por == administrador_catalogo and directa.fecha_creacion
    limite = LimiteVertido.objects.get(prueba=directa)
    assert (limite.tipo_vertido, limite.limite_max, limite.norma) == ("cloacal", "20", "AGOSBA")
    formula = crear(
        administrador_catalogo,
        datos_prueba(codigo="TEST-FOR", tipo_calculo="FORMULA", formula="{TEST-DIR}*2"),
    )
    assert formula.es_calculada
    assert not LimiteVertido.objects.filter(prueba=formula).exists()


@pytest.mark.parametrize(
    ("cambios", "campo"),
    [
        ({"tipo_calculo": "FORMULA", "formula": "x*"}, "formula"),
        ({"tipo_calculo": "FORMULA", "formula": "{NO-EXISTE}*2"}, "formula"),
        ({"tipo_calculo": "FORMULA", "formula": "{TEST-DIR}*2"}, "formula"),
        ({"tipo_calculo": "FORMULA", "formula": ""}, "formula"),
        ({"codigo": "ph"}, "codigo"),
        ({"limite_max": "NE"}, "limite_max"),
        ({"limite_min": "20", "limite_max": "10"}, "limite_min"),
        ({"canal_limite_max": "SOE"}, "canal_limite_max"),
    ],
)
def test_alta_rechaza(administrador_catalogo, datos_prueba, cambios, campo):
    Prueba.objects.create(codigo="PH", nombre="pH")
    antes = Prueba.objects.count()
    with pytest.raises(gestion.DatosInvalidos) as error:
        crear(administrador_catalogo, datos_prueba(**cambios))
    assert campo in error.value.errores
    assert Prueba.objects.count() == antes


# --- US2: sin uso ----------------------------------------------------------------------------


def test_sin_uso_edita_todo(administrador_catalogo, datos_prueba):
    Prueba.objects.create(codigo="BASE", nombre="Base")
    prueba = crear(administrador_catalogo, datos_prueba())
    operar(
        administrador_catalogo,
        prueba,
        "editar",
        datos_prueba(
            codigo="TEST-NUEVO",
            nombre="Renombrada",
            tipo_calculo="FORMULA",
            formula="{BASE}+1",
            unidad="UpH",
        ),
    )
    prueba.refresh_from_db()
    assert (prueba.codigo, prueba.nombre, prueba.formula, prueba.unidad) == (
        "TEST-NUEVO",
        "Renombrada",
        "{BASE}+1",
        "UpH",
    )
    assert prueba.version == 2 and prueba.modificada_por == administrador_catalogo
    operar(administrador_catalogo, prueba, "editar", datos_prueba(codigo="TEST-NUEVO"))
    prueba.refresh_from_db()
    assert prueba.tipo_calculo == "DIRECTO" and prueba.formula == "" and not prueba.es_calculada


def test_sin_uso_elimina(administrador_catalogo, datos_prueba):
    prueba = crear(administrador_catalogo, datos_prueba(canal_limite_max="5"))
    operar(administrador_catalogo, prueba, "eliminar")
    assert not Prueba.objects.filter(pk=prueba.pk).exists()
    assert not LimiteVertido.objects.exists()


def test_referenciada(administrador_catalogo, datos_prueba):
    base = crear(administrador_catalogo, datos_prueba())
    crear(
        administrador_catalogo,
        datos_prueba(codigo="TEST-FOR", tipo_calculo="FORMULA", formula="{TEST-DIR}*2"),
    )
    with pytest.raises(gestion.PruebaReferenciada) as error:
        operar(administrador_catalogo, base, "eliminar")
    assert error.value.codigos == ["TEST-FOR"]
    with pytest.raises(gestion.PruebaReferenciada):
        operar(administrador_catalogo, base, "editar", datos_prueba(codigo="OTRO"))
    operar(administrador_catalogo, base, "editar", datos_prueba(nombre="Sí se puede"))
    base.refresh_from_db()
    assert base.nombre == "Sí se puede"


# --- US3: en uso -----------------------------------------------------------------------------


def test_en_uso_solo_limites(administrador_catalogo, prueba_en_estudio):
    datos = gestion.datos_de(prueba_en_estudio)
    datos.update(limite_max="8", norma="Nueva", limite_deteccion="0.5", canal_limite_max="3")
    datos["observacion"] = "Cambio de norma"
    operar(administrador_catalogo, prueba_en_estudio, "editar", datos)
    prueba_en_estudio.refresh_from_db()
    assert (prueba_en_estudio.limite_max, prueba_en_estudio.norma) == ("8", "Nueva")
    assert LimiteVertido.objects.get(prueba=prueba_en_estudio).limite_max == "3"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("codigo", "OTRO"),
        ("nombre", "Otro nombre"),
        ("tipo_calculo", "FORMULA"),
        ("unidad", "UpH"),
        ("unidad_medicion", "ml"),
    ],
)
def test_en_uso_bloquea_metodo(administrador_catalogo, prueba_en_tipo, campo, valor):
    datos = gestion.datos_de(prueba_en_tipo)
    datos[campo] = valor
    if campo == "tipo_calculo":
        datos["formula"] = "x*2"
    with pytest.raises(gestion.PruebaEnUso):
        operar(administrador_catalogo, prueba_en_tipo, "editar", datos)
    prueba_en_tipo.refresh_from_db()
    assert prueba_en_tipo.version == 1


def test_paso_a_estar_en_uso(administrador_catalogo, datos_prueba):
    from estudios.models import TipoEstudio

    prueba = crear(administrador_catalogo, datos_prueba())
    version = prueba.version
    TipoEstudio.objects.create(nombre="Lo agregó otro").pruebas.set([prueba])
    with pytest.raises(gestion.PruebaEnUso):
        gestion.gestionar_prueba(
            usuario=administrador_catalogo,
            operacion="editar",
            prueba_id=prueba.pk,
            version_esperada=version,
            datos=datos_prueba(nombre="Cambio de método"),
        )


def test_en_uso_no_elimina(administrador_catalogo, prueba_en_tipo):
    with pytest.raises(gestion.PruebaEnUso):
        operar(administrador_catalogo, prueba_en_tipo, "eliminar")
    assert Prueba.objects.filter(pk=prueba_en_tipo.pk).exists()


def test_historial_intacto(administrador_catalogo, estudio_de, empleado, bioquimico):
    estudio = estudio_de("CL-")
    cargar(estudio, empleado, CL_="40")
    validar(estudio, bioquimico, "CL-")
    informe = emitir_informe(estudio.pk, bioquimico)
    validacion = Validacion.objects.get(asignacion__estudio=estudio)
    copia, limite_validado = informe.contenido, validacion.limite_max
    cloruro = Prueba.objects.get(codigo="CL-")
    datos = gestion.datos_de(cloruro)
    datos["limite_max"] = "500"
    operar(administrador_catalogo, cloruro, "editar", datos)
    validacion.refresh_from_db()
    assert validacion.limite_max == limite_validado
    assert Informe.objects.get(pk=informe.pk).contenido == copia
    nuevo = estudio_de("CL-")
    cargar(nuevo, empleado, CL_="40")
    validar(nuevo, bioquimico, "CL-")
    assert Validacion.objects.get(asignacion__estudio=nuevo).limite_max == "500"


# --- Polish: auditoría -----------------------------------------------------------------------


def test_auditoria(administrador_catalogo, datos_prueba, prueba_libre):
    prueba = crear(administrador_catalogo, datos_prueba())
    assert prueba.modificada_por is None
    operar(administrador_catalogo, prueba, "desactivar")
    prueba.refresh_from_db()
    assert prueba.modificada_por == administrador_catalogo and prueba.fecha_modificacion
    assert prueba_libre.creada_por is None  # anteriores o importadas: «Sin registro»


def test_servicio_revalida(empleado, datos_prueba):
    with pytest.raises(gestion.NoAutorizado):
        crear(empleado, datos_prueba())
    assert not Prueba.objects.exists()
