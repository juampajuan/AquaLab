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


# --- detalle_estudio: qué no cumple (US2) ---


def test_solo_fuera_de_norma(empleado, estudio_completo):
    """US2 Esc. 1: solo las fuera de norma, con resultado, unidad, límite y norma."""
    salida = ejecutar(
        empleado, "detalle_estudio", numero=estudio_completo.pk, solo_fuera_de_norma=True
    ).salida
    datos = salida["datos"]
    assert [p["codigo"] for p in datos["pruebas"]] == ["CL-"]
    [cloruro] = datos["pruebas"]
    assert (cloruro["resultado"], cloruro["unidad"]) == ("400", "mg/l")
    assert (cloruro["limite"], cloruro["evaluacion"]) == ("máx. 350.0", "Fuera de norma")
    assert cloruro["norma"]
    assert datos["resumen"] == {"sin_resultado": 1, "sin_limite_comparable": 1, "total": 6}


def test_nada_fuera_de_norma(empleado, estudio_de):
    """US2 Esc. 2: ninguna fuera de norma; el resumen cuenta las que no se pudieron evaluar."""
    from estudios.tests.utiles import cargar

    estudio = estudio_de("PH", "COND", "TEMPERATURA")
    cargar(estudio, empleado, {"PH": "7.2", "COND": "500"})
    datos = ejecutar(
        empleado, "detalle_estudio", numero=estudio.pk, solo_fuera_de_norma=True
    ).salida["datos"]
    assert datos["pruebas"] == []
    assert datos["resumen"] == {"sin_resultado": 1, "sin_limite_comparable": 1, "total": 3}


def test_sin_filtro_no_hay_resumen(empleado, estudio_completo):
    datos = ejecutar(empleado, "detalle_estudio", numero=estudio_completo.pk).salida["datos"]
    assert "resumen" not in datos
    assert len(datos["pruebas"]) == 6


def test_detalle_por_texto_origen(empleado, escuela):
    """Por el origen, sin acentos ni mayúsculas; con una sola coincidencia, el detalle."""
    salida = ejecutar(empleado, "detalle_estudio", texto="ESCUELA TECNICA").salida
    assert len(salida["datos"]["coincidencias"]) == 2
    salida = ejecutar(empleado, "detalle_estudio", texto="200101").salida
    assert salida["datos"]["numero"] == escuela["viejo"].pk
    assert {p["codigo"] for p in salida["datos"]["pruebas"]} == {"PH", "CL-"}


def test_detalle_varias_coincidencias(empleado, escuela):
    """US2 Esc. 3: las coincidencias, más recientes primero, con referencias y pedido de elegir."""
    ejecucion = ejecutar(empleado, "detalle_estudio", texto="escuela técnica n° 12")
    salida = ejecucion.salida
    assert salida["encontrado"] is True
    assert salida["mensaje"] == "Hay varios estudios que coinciden; pedí cuál."
    assert (salida["total"], salida["mostrados"]) == (2, 2)
    coincidencias = salida["datos"]["coincidencias"]
    assert [c["numero"] for c in coincidencias] == [escuela["nuevo"].pk, escuela["viejo"].pk]
    assert coincidencias[0] == {
        "numero": escuela["nuevo"].pk,
        "numero_pi": 200102,
        "origen": "Escuela Técnica N° 12",
        "tipo": escuela["nuevo"].tipo_nombre_snapshot,
        "fecha": HOY,
        "estado": "Finalizado",
    }
    assert referencias(ejecucion) == [
        ("estudio", escuela["nuevo"].pk),
        ("estudio", escuela["viejo"].pk),
    ]


def test_detalle_varias_coincidencias_por_pi(empleado, estudio_completo, muestra):
    _otro_estudio(muestra, empleado)
    salida = ejecutar(empleado, "detalle_estudio", numero_pi=200001).salida
    assert len(salida["datos"]["coincidencias"]) == 2


def test_detalle_coincidencias_hasta_10(empleado, muestra, catalogo):
    for _ in range(12):
        _otro_estudio(muestra, empleado)
    salida = ejecutar(empleado, "detalle_estudio", texto="Muestra test").salida
    assert (salida["total"], salida["mostrados"]) == (12, 10)
    assert len(salida["datos"]["coincidencias"]) == 10


def test_detalle_texto_sin_coincidencias(empleado, escuela):
    """US2 Esc. 4."""
    salida = ejecutar(empleado, "detalle_estudio", texto="Pozo 9").salida
    assert salida == {
        "encontrado": False,
        "mensaje": "No hay estudios que coincidan con «Pozo 9».",
    }


# --- clientes (US3) ---


def test_buscar_cliente(empleado, lacteos, cliente_a):
    from clientes.models import Cliente

    inactivo = Cliente.objects.create(
        razon_social="Lácteos del Norte",
        tipo_documento="CUIT",
        numero_documento="30711111112",
        email="norte@lacteos.test",
        activo=False,
    )
    ejecucion = ejecutar(empleado, "buscar_cliente", texto="lacteos")
    salida = ejecucion.salida
    assert salida["encontrado"] is True
    assert salida["datos"]["clientes"] == [
        {"id": lacteos["cliente"].pk, "nombre": "Lácteos del Sur S.A.", "activo": True},
        {"id": inactivo.pk, "nombre": "Lácteos del Norte", "activo": False},
    ]
    assert referencias(ejecucion) == [
        ("cliente", lacteos["cliente"].pk),
        ("historial", lacteos["cliente"].pk),
    ]


def test_buscar_cliente_inexistente(empleado, lacteos):
    salida = ejecutar(empleado, "buscar_cliente", texto="Aguas del Norte").salida
    assert salida == {
        "encontrado": False,
        "mensaje": "No hay clientes que coincidan con «Aguas del Norte».",
    }


def test_estudios_de_cliente(empleado, lacteos):
    """US3 Esc. 1–2: los 10 más recientes en el orden del historial, con el total."""
    ejecucion = ejecutar(empleado, "estudios_de_cliente", cliente="Lácteos del Sur")
    salida = ejecucion.salida
    assert salida["encontrado"] is True
    assert (salida["total"], salida["mostrados"]) == (12, 10)
    datos = salida["datos"]
    assert datos["cliente"] == "Lácteos del Sur S.A."
    estudios = lacteos["estudios"]
    assert [e["numero"] for e in datos["estudios"]] == [e.pk for e in estudios[:10]]
    primero = datos["estudios"][0]
    assert primero == {
        "numero": estudios[0].pk,
        "numero_pi": 200200,
        "origen": "Pozo de la planta",
        "tipo": estudios[0].tipo_nombre_snapshot,
        "fecha_ingreso": HOY,
        "estado": "Finalizado",
        "con_informe": False,
    }
    assert datos["estudios"][1]["estado"] == "En proceso"
    assert ejecucion.avisos == [
        "Lácteos del Sur S.A. tiene 12 estudios; se muestran los 10 más recientes. "
        "El resto está en su historial."
    ]
    assert [(r.tipo, r.pk) for r in ejecucion.primeras] == [("historial", lacteos["cliente"].pk)]
    tipos = [r.tipo for r in ejecucion.referencias]
    assert tipos[:2] == ["cliente", "historial"]
    assert tipos.count("estudio") == 10


def test_estudios_de_cliente_pocos_sin_aviso(empleado, estudio_completo, cliente_a):
    ejecucion = ejecutar(empleado, "estudios_de_cliente", cliente_id=cliente_a.pk)
    assert (ejecucion.salida["total"], ejecucion.salida["mostrados"]) == (1, 1)
    assert ejecucion.avisos == []
    assert ejecucion.primeras == []


def test_cliente_inexistente(empleado, lacteos):
    """US3 Esc. 3."""
    assert ejecutar(empleado, "estudios_de_cliente", cliente="Aguas del Norte").salida == {
        "encontrado": False,
        "mensaje": "No hay ningún cliente que coincida con «Aguas del Norte».",
    }
    assert ejecutar(empleado, "estudios_de_cliente", cliente_id=999999).salida == {
        "encontrado": False,
        "mensaje": "No hay ningún cliente con ese identificador.",
    }
    assert ejecutar(empleado, "estudios_de_cliente").salida["encontrado"] is False


def test_varios_clientes(empleado, lacteos):
    """US3 Esc. 4: se listan para elegir, sin estudios."""
    from clientes.models import Cliente

    otro = Cliente.objects.create(
        razon_social="Lácteos del Sur Norte",
        tipo_documento="CUIT",
        numero_documento="30722222223",
        email="otro@lacteos.test",
    )
    ejecucion = ejecutar(empleado, "estudios_de_cliente", cliente="lacteos del sur")
    salida = ejecucion.salida
    assert salida["encontrado"] is True
    assert salida["mensaje"] == "Hay varios clientes con ese nombre; pedí cuál."
    assert [c["id"] for c in salida["datos"]["coincidencias"]] == sorted(
        [lacteos["cliente"].pk, otro.pk],
        key=lambda pk: Cliente.objects.get(pk=pk).razon_social,
    )
    assert "estudios" not in salida["datos"]


def test_cliente_inactivo(empleado, lacteos):
    """US3 Esc. 5: ni estudios ni enlaces a su ficha o historial."""
    cliente = lacteos["cliente"]
    cliente.activo = False
    cliente.save()
    ejecucion = ejecutar(empleado, "estudios_de_cliente", cliente_id=cliente.pk)
    assert ejecucion.salida == {
        "encontrado": False,
        "mensaje": "El cliente Lácteos del Sur S.A. está inactivo.",
    }
    assert ejecucion.referencias == []


def test_por_cliente_id(empleado, lacteos):
    buscado = ejecutar(empleado, "buscar_cliente", texto="Lácteos").salida
    cliente_id = buscado["datos"]["clientes"][0]["id"]
    salida = ejecutar(empleado, "estudios_de_cliente", cliente_id=cliente_id).salida
    assert salida["total"] == 12


def test_permisos_como_pantallas(cliente_http, empleado, lacteos):
    """FR-010: cada herramienta da acceso o rechazo igual que su pantalla."""
    from django.urls import reverse

    cliente = lacteos["cliente"]
    estudio = lacteos["estudios"][0]
    cliente.activo = False
    cliente.save()
    assert cliente_http.get(reverse("clientes:detalle", args=[cliente.pk])).status_code == 302
    assert cliente_http.get(reverse("clientes:historial", args=[cliente.pk])).status_code == 302
    assert (
        ejecutar(empleado, "estudios_de_cliente", cliente_id=cliente.pk).salida["encontrado"]
        is False
    )
    assert (
        cliente_http.get(reverse("muestras:detalle", args=[estudio.muestra_id])).status_code == 200
    )
    assert ejecutar(empleado, "buscar_muestra", numero_pi=200200).salida["encontrado"] is True
    assert cliente_http.get(reverse("estudios:detalle", args=[estudio.pk])).status_code == 200
    assert ejecutar(empleado, "detalle_estudio", numero=estudio.pk).salida["encontrado"] is True


def test_herramientas_rechazan_usuario_inactivo(empleado, estudio_completo, cliente_a):
    empleado.is_active = False
    empleado.save()
    for nombre, argumentos in (
        ("buscar_muestra", {"numero_pi": 200001}),
        ("detalle_estudio", {"numero": estudio_completo.pk}),
        ("estudios_de_cliente", {"cliente_id": cliente_a.pk}),
    ):
        assert ejecutar(empleado, nombre, **argumentos).salida["encontrado"] is False, nombre
