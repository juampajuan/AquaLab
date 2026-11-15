"""Herramientas de solo lectura (contracts/herramientas.md) contra datos de prueba."""

import uuid

import pytest
from django.urls import reverse
from django.utils import timezone

from asistente.enlaces import Referencia

from .conftest import ejecutar

pytestmark = pytest.mark.django_db

HOY = timezone.localdate().strftime("%d/%m/%Y")


def referencias(ejecucion):
    return [(r.tipo, r.pk) for r in ejecucion.referencias]


# --- buscar_muestra (US1) ---


def test_buscar_muestra_por_pi(empleado, estudio_completo, muestra):
    """US1 Esc. 2: los datos de la ficha de la muestra."""
    otro = _otro_estudio(muestra, empleado)
    ejecucion = ejecutar(empleado, "buscar_muestra", numero_pi=200001)
    assert ejecucion.valida
    salida = ejecucion.salida
    assert salida["encontrado"] is True
    datos = salida["datos"]
    assert datos == {
        "numero_pi": 200001,
        "nombre": "Muestra test",
        "cliente": "Cliente de test",
        "origen": "Origen de test",
        "estado": "Ingresada",
        "fecha_muestreo": HOY,
        "fecha_ingreso": HOY,
        "tipo_vertido": "Agua",
        "sitio_extraccion": "Sitio test",
        "total_estudios": 2,
        "estudios": [
            {
                "numero": otro.pk,
                "tipo": otro.tipo_nombre_snapshot,
                "estado": "Sin iniciar",
                "pruebas_completadas": 0,
                "total_pruebas": 1,
                "con_informe": False,
            },
            {
                "numero": estudio_completo.pk,
                "tipo": estudio_completo.tipo_nombre_snapshot,
                "estado": "En proceso",
                "pruebas_completadas": 2,
                "total_pruebas": 6,
                "con_informe": False,
            },
        ],
    }


def _otro_estudio(muestra, empleado):
    from estudios.models import TipoEstudio
    from estudios.servicios import crear_estudio
    from pruebas.models import Prueba

    tipo = TipoEstudio.objects.create(nombre=f"Otro {uuid.uuid4()}")
    tipo.pruebas.set(Prueba.objects.filter(codigo="PH"))
    return crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra.pk,
            "tipo": tipo.pk,
            "version": tipo.version,
        },
        empleado,
    )


def test_buscar_muestra_inexistente(empleado, estudio_completo):
    """US1 Esc. 4."""
    ejecucion = ejecutar(empleado, "buscar_muestra", numero_pi=200999)
    assert ejecucion.salida == {
        "encontrado": False,
        "mensaje": "No hay ninguna muestra con el N° PI 200999.",
    }
    assert ejecucion.referencias == []


def test_buscar_muestra_pi_formato_invalido(empleado, estudio_completo):
    """«PI 12» o un número fuera de rango: no encontrada, sin error."""
    for numero in (12, 0, -5, 10**12):
        salida = ejecutar(empleado, "buscar_muestra", numero_pi=numero).salida
        assert salida["encontrado"] is False
        assert salida["mensaje"] == f"No hay ninguna muestra con el N° PI {numero}."


def test_buscar_muestra_sin_criterio(empleado):
    salida = ejecutar(empleado, "buscar_muestra").salida
    assert salida["encontrado"] is False


def test_buscar_muestra_por_texto(empleado, estudio_completo):
    """Por nombre de la muestra, del origen o del cliente, sin acentos ni mayúsculas."""
    for texto in ("muestra TEST", "orígen de test", "CLIENTE de"):
        salida = ejecutar(empleado, "buscar_muestra", texto=texto).salida
        assert salida["encontrado"] is True, texto
        assert salida["total"] == 1
        [encontrada] = salida["datos"]["muestras"]
        assert encontrada["numero_pi"] == 200001
        assert encontrada["total_estudios"] == 1
    assert ejecutar(empleado, "buscar_muestra", texto="nada parecido").salida["encontrado"] is False


def test_buscar_muestra_muchos_estudios(empleado, muestra, catalogo):
    """US1 Esc. 7: con 7 estudios, los 5 más recientes, el total y el aviso."""
    estudios = [_otro_estudio(muestra, empleado) for _ in range(7)]
    ejecucion = ejecutar(empleado, "buscar_muestra", numero_pi=200001)
    datos = ejecucion.salida["datos"]
    assert datos["total_estudios"] == 7
    assert [e["numero"] for e in datos["estudios"]] == [e.pk for e in reversed(estudios)][:5]
    assert ejecucion.salida["mensaje"] == (
        "La muestra tiene 7 estudios; se detallan los 5 más recientes."
    )
    assert ejecucion.avisos == [
        "La muestra PI 200001 tiene 7 estudios; se detallan los 5 más recientes. "
        "El resto está en la ficha de la muestra."
    ]
    assert [(r.tipo, r.pk) for r in ejecucion.primeras] == [("muestra", muestra.pk)]


def test_buscar_muestra_referencias(empleado, estudio_completo, muestra, cliente_a):
    ejecucion = ejecutar(empleado, "buscar_muestra", numero_pi=200001)
    assert referencias(ejecucion) == [
        ("muestra", muestra.pk),
        ("estudio", estudio_completo.pk),
        ("cliente", cliente_a.pk),
    ]
    muestra_ref = ejecucion.referencias[0]
    assert muestra_ref.etiqueta == "PI 200001"
    assert "200001" in muestra_ref.claves
    assert ejecucion.referencias[1].etiqueta == f"Estudio {estudio_completo.pk}"


def test_buscar_muestra_cliente_inactivo_sin_referencia(empleado, estudio_completo, cliente_a):
    cliente_a.activo = False
    cliente_a.save()
    ejecucion = ejecutar(empleado, "buscar_muestra", numero_pi=200001)
    assert ejecucion.salida["encontrado"] is True
    assert "cliente" not in [r.tipo for r in ejecucion.referencias]


# --- detalle_estudio (US1) ---


def pruebas_por_codigo(salida):
    return {p["codigo"]: p for p in salida["datos"]["pruebas"]}


def test_detalle_estudio_por_numero(empleado, estudio_completo):
    salida = ejecutar(empleado, "detalle_estudio", numero=estudio_completo.pk).salida
    assert salida["encontrado"] is True
    datos = salida["datos"]
    assert {k: v for k, v in datos.items() if k != "pruebas"} == {
        "numero": estudio_completo.pk,
        "numero_pi": 200001,
        "cliente": "Cliente de test",
        "origen": "Origen de test",
        "tipo": estudio_completo.tipo_nombre_snapshot,
        "estado": "En proceso",
        "fecha_creacion": HOY,
        "tipo_vertido": "Agua",
        "con_informe": False,
    }
    pruebas = pruebas_por_codigo(salida)
    assert list(pruebas) == sorted(pruebas)
    assert pruebas["PH"] == {
        "codigo": "PH",
        "nombre": "pH",
        "estado": "Completada",
        "resultado": "7,2",
        "unidad": "UpH",
        "sin_resultado": "",
        "fuera_de_rango_curva": False,
        "evaluacion": "Cumple",
        "limite": "6.4 a 8.5",
        "norma": "4500• H+ B",
        "origen_limites": "",
        "validada": True,
        "fecha_validacion": HOY,
    }
    assert pruebas["CL-"]["resultado"] == "400"
    assert pruebas["CL-"]["unidad"] == "mg/l"
    assert pruebas["CL-"]["evaluacion"] == "Fuera de norma"
    assert pruebas["CL-"]["limite"] == "máx. 350.0"


def test_detalle_estudio_sin_resultado(empleado, estudio_completo):
    """US1 Esc. 5: una prueba Pendiente no tiene resultado ni evaluación, y dice el motivo."""
    temperatura = pruebas_por_codigo(
        ejecutar(empleado, "detalle_estudio", numero=estudio_completo.pk).salida
    )["TEMPERATURA"]
    assert temperatura["estado"] == "Pendiente"
    assert temperatura["resultado"] == ""
    assert temperatura["evaluacion"] == ""
    assert temperatura["sin_resultado"]
    assert temperatura["validada"] is False


def test_detalle_estudio_sin_validar(empleado, estudio_completo):
    """US1 Esc. 6: Cargada → sin validar y con la evaluación del catálogo, como el detalle."""
    cond = pruebas_por_codigo(
        ejecutar(empleado, "detalle_estudio", numero=estudio_completo.pk).salida
    )["COND"]
    assert cond["estado"] == "Por validar"
    assert cond["validada"] is False
    assert cond["fecha_validacion"] == ""
    assert cond["resultado"] == "500"
    assert cond["evaluacion"] == "Sin límite comparable"


def test_detalle_presencia_y_ld(empleado, estudio_completo):
    pruebas = pruebas_por_codigo(
        ejecutar(empleado, "detalle_estudio", numero=estudio_completo.pk).salida
    )
    assert pruebas["ECOLI"]["resultado"] == "Ausente"
    assert pruebas["ECOLI"]["unidad"] == ""
    assert pruebas["ECOLI"]["evaluacion"] == "Cumple"
    assert pruebas["TURBIDEZ"]["resultado"] == "< 0,1"
    for prueba in pruebas.values():
        assert prueba["resultado"] not in ("0", "1")


def test_detalle_presente(empleado, estudio_de):
    from estudios.tests.utiles import cargar

    estudio = estudio_de("ECOLI")
    cargar(estudio, empleado, {"ECOLI": "1"})
    ecoli = pruebas_por_codigo(ejecutar(empleado, "detalle_estudio", numero=estudio.pk).salida)[
        "ECOLI"
    ]
    assert ecoli["resultado"] == "Presente"
    assert ecoli["evaluacion"] == "Fuera de norma"


def test_detalle_coma_decimal(empleado, estudio_de):
    from estudios.tests.utiles import cargar

    estudio = estudio_de("COND")
    cargar(estudio, empleado, {"COND": "12.375"})
    cond = pruebas_por_codigo(ejecutar(empleado, "detalle_estudio", numero=estudio.pk).salida)[
        "COND"
    ]
    assert cond["resultado"] == "12,375"


def test_detalle_con_informe(empleado, crear_pendiente):
    estudio = crear_pendiente(cantidad=1, cargadas=1, informado=True)
    ejecucion = ejecutar(empleado, "detalle_estudio", numero=estudio.pk)
    assert ejecucion.salida["datos"]["con_informe"] is True
    assert ("informe", estudio.pk) in referencias(ejecucion)
    informe = ejecucion.referencias[referencias(ejecucion).index(("informe", estudio.pk))]
    assert informe.url() == reverse("informes:ver", args=[estudio.pk])


def test_detalle_estudio_inexistente(empleado):
    salida = ejecutar(empleado, "detalle_estudio", numero=999999).salida
    assert salida == {"encontrado": False, "mensaje": "No hay ningún estudio con el número 999999."}


def test_detalle_por_pi_con_un_estudio(empleado, estudio_completo):
    salida = ejecutar(empleado, "detalle_estudio", numero_pi=200001).salida
    assert salida["datos"]["numero"] == estudio_completo.pk


def test_detalle_referencias(empleado, estudio_completo, muestra, cliente_a):
    ejecucion = ejecutar(empleado, "detalle_estudio", numero=estudio_completo.pk)
    assert referencias(ejecucion) == [
        ("estudio", estudio_completo.pk),
        ("muestra", muestra.pk),
        ("cliente", cliente_a.pk),
    ]


def test_salidas_sin_datos_de_contacto_ni_usuarios(empleado, estudio_completo, cliente_a):
    texto = str(
        [
            ejecutar(empleado, "buscar_muestra", numero_pi=200001).salida,
            ejecutar(empleado, "detalle_estudio", numero=estudio_completo.pk).salida,
        ]
    )
    for prohibido in (cliente_a.email, cliente_a.numero_documento, empleado.email):
        assert prohibido not in texto


def test_definiciones_de_us1():
    from asistente import herramientas

    nombres = {d["function"]["name"] for d in herramientas.definiciones()}
    assert {"buscar_muestra", "detalle_estudio"} <= nombres
    for definicion in herramientas.definiciones():
        assert definicion["type"] == "function"
        assert definicion["function"]["description"]
        assert definicion["function"]["parameters"]["type"] == "object"


def test_referencia_url():
    assert Referencia("muestra", 3, "PI 1").url() == "/muestras/3/"
