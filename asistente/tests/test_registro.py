"""Herramientas `preparar_muestra` y `preparar_estudio` (US 10.3, contracts/herramientas.md)."""

import datetime
import json
from urllib.parse import parse_qsl, urlsplit

import pytest
from django.utils import timezone

from .conftest import ejecutar as ejecutar_herramienta

pytestmark = pytest.mark.django_db

AVISO_MUESTRA = "La muestra se registra recién cuando confirmes en el formulario."
AVISO_ESTUDIO = "El estudio se crea recién cuando confirmes en la pantalla de crear estudio."


@pytest.fixture
def datos():
    """«Lácteos del Sur S.A.» (con datos de contacto) y su catálogo de tipos."""
    from clientes.models import Cliente
    from estudios.models import TipoEstudio
    from muestras.models import Origen

    cliente = Cliente.objects.create(
        razon_social="Lácteos del Sur S.A.",
        tipo_documento="CUIT",
        numero_documento="30712345675",
        email="contacto@lacteos.test",
        telefono="+54 11 5555-0101",
        domicilio="Ruta 5 km 112",
    )
    return {
        "cliente": cliente,
        "pozo1": Origen.objects.create(cliente=cliente, nombre="Pozo 1"),
        "pozo2": Origen.objects.create(cliente=cliente, nombre="Pozo 2"),
        "tanque": Origen.objects.create(cliente=cliente, nombre="Tanque elevado"),
        "fq": TipoEstudio.objects.create(nombre="Físico-químico básico"),
        "bact": TipoEstudio.objects.create(nombre="Bacteriológico básico"),
        "vuelco": TipoEstudio.objects.create(nombre="Vuelco a colectora", activo=False),
    }


@pytest.fixture
def hoy():
    return timezone.localdate()


def ejecutar(usuario, herramienta, **argumentos):
    """Como `conftest.ejecutar`, pero admite el argumento `nombre` de la muestra."""
    from asistente import herramientas

    if "nombre" not in argumentos:
        return ejecutar_herramienta(usuario, herramienta, **argumentos)
    return herramientas.ejecutar(usuario, herramienta, json.dumps(argumentos))


def completo(**extra):
    return {
        "cliente": "Lácteos del Sur",
        "origen": "pozo 2",
        "tipo_estudio": "físico-químico básico",
        "tipo_vertido": "agua",
        "fecha_muestreo": "ayer",
        "fecha_ingreso": "hoy",
        "sitio_extraccion": "Boca del pozo",
        **extra,
    }


def parametros(enlace):
    partes = urlsplit(enlace["url"])
    return partes.path, dict(parse_qsl(partes.query))


def enlaces(lista):
    return [r.enlace() for r in lista]


# --- US1 (T012) ---


def test_faltan_vertido_fechas_y_sitio(empleado, datos):
    resultado = ejecutar(
        empleado,
        "preparar_muestra",
        cliente="Lácteos del Sur",
        origen="pozo 2",
        tipo_estudio="físico-químico básico",
    )
    salida = resultado.salida
    assert salida["encontrado"] is True
    assert salida["listo"] is False
    assert salida["faltan"] == [
        "tipo de vertido",
        "fecha de muestreo",
        "fecha de ingreso",
        "sitio de extracción",
    ]
    assert salida["problemas"] == []
    # El vertido se elige: Agua, Cloacal o Canal (nunca se supone).
    assert salida["elegir"] == "tipo_vertido"
    assert enlaces(resultado.opciones) == [
        {"etiqueta": "Agua", "pregunta": "El tipo de vertido es Agua"},
        {"etiqueta": "Cloacal", "pregunta": "El tipo de vertido es Cloacal"},
        {"etiqueta": "Canal", "pregunta": "El tipo de vertido es Canal"},
    ]
    assert salida["resuelto"] == {
        "cliente": "Lácteos del Sur S.A.",
        "origen": "Pozo 2",
        "tipo_estudio": "Físico-químico básico",
    }
    assert resultado.primeras == []
    # Resumen de lo resuelto para que sobreviva en el historial (R10).
    assert resultado.avisos == [
        "Hasta ahora: Cliente: Lácteos del Sur S.A. · Origen: Pozo 2 · Tipo de estudio: "
        "Físico-químico básico."
    ]


def test_listo_con_enlace_precargado(empleado, datos, hoy):
    resultado = ejecutar(empleado, "preparar_muestra", **completo())
    salida = resultado.salida
    ayer = hoy - datetime.timedelta(days=1)
    assert salida["listo"] is True
    assert salida["faltan"] == [] and salida["problemas"] == []
    assert salida["resuelto"]["fecha_muestreo"] == ayer.strftime("%d/%m/%Y")
    assert salida["resuelto"]["fecha_ingreso"] == hoy.strftime("%d/%m/%Y")
    [enlace] = enlaces(resultado.primeras)
    assert enlace["etiqueta"] == "Revisar y registrar la muestra"
    assert enlace["minimizar"] is True
    ruta, consulta = parametros(enlace)
    assert ruta == "/muestras/registrar/"
    assert consulta == {
        "cliente": str(datos["cliente"].pk),
        "origen": str(datos["pozo2"].pk),
        "fecha_muestreo": ayer.isoformat(),
        "fecha_ingreso": hoy.isoformat(),
        "sitio_extraccion": "Boca del pozo",
        "tipo_vertido": "agua",
        "tipo_estudio": str(datos["fq"].pk),
    }
    assert salida["resuelto"]["tipo_vertido"] == "Agua"
    assert salida["resuelto"]["sitio_extraccion"] == "Boca del pozo"
    assert resultado.avisos == [AVISO_MUESTRA]


def test_origen_sin_mayusculas_ni_acentos(empleado, datos):
    resultado = ejecutar(empleado, "preparar_muestra", **completo(origen="TANQUE ELEVADO"))
    assert resultado.salida["resuelto"]["origen"] == "Tanque elevado"


def test_sin_tipo_ofrece_solo_muestra_primero(empleado, datos):
    argumentos = completo()
    del argumentos["tipo_estudio"]
    resultado = ejecutar(empleado, "preparar_muestra", **argumentos)
    salida = resultado.salida
    assert salida["listo"] is False
    assert salida["faltan"] == ["tipo de estudio"]
    assert salida["elegir"] == "tipo_estudio"
    opciones = enlaces(resultado.opciones)
    assert opciones[0] == {
        "etiqueta": "Solo registrar la muestra",
        "pregunta": "Solo registrar la muestra, sin estudio",
    }
    assert opciones[1:] == [
        {
            "etiqueta": "Bacteriológico básico",
            "pregunta": "El tipo de estudio es Bacteriológico básico",
        },
        {
            "etiqueta": "Físico-químico básico",
            "pregunta": "El tipo de estudio es Físico-químico básico",
        },
    ]


def test_solo_muestra(empleado, datos):
    argumentos = completo(solo_muestra=True)
    del argumentos["tipo_estudio"]
    resultado = ejecutar(empleado, "preparar_muestra", **argumentos)
    assert resultado.salida["listo"] is True
    assert resultado.salida["resuelto"]["tipo_estudio"] == "sin estudio"
    _, consulta = parametros(resultado.primeras[0].enlace())
    assert "tipo_estudio" not in consulta


@pytest.mark.parametrize(
    "fechas, mensaje",
    [
        (
            {"fecha_muestreo": "hoy", "fecha_ingreso": "ayer"},
            "La fecha de muestreo no puede ser posterior a la fecha de ingreso.",
        ),
        ({"fecha_muestreo": "ayer", "fecha_ingreso": "31/12/2099"}, "posterior a hoy"),
    ],
)
def test_fechas_que_rechaza_el_formulario(empleado, datos, fechas, mensaje):
    resultado = ejecutar(empleado, "preparar_muestra", **completo(**fechas))
    salida = resultado.salida
    assert salida["listo"] is False
    assert any(mensaje in p for p in salida["problemas"])
    assert resultado.primeras == []


def test_fecha_ilegible(empleado, datos):
    resultado = ejecutar(empleado, "preparar_muestra", **completo(fecha_muestreo="el martes"))
    assert resultado.salida["faltan"] == ["fecha de muestreo (no entendí «el martes»)"]
    assert resultado.salida["listo"] is False


def test_datos_opcionales_viajan_en_el_enlace(empleado, datos):
    resultado = ejecutar(
        empleado,
        "preparar_muestra",
        **completo(tipo_vertido="Cloacal", nombre="Control", responsable_muestreo="Pedro"),
    )
    _, consulta = parametros(resultado.primeras[0].enlace())
    assert consulta["tipo_vertido"] == "cloacal"
    assert consulta["nombre"] == "Control"
    assert consulta["responsable_muestreo"] == "Pedro"


def test_sin_opcionales_no_viajan(empleado, datos):
    _, consulta = parametros(
        ejecutar(empleado, "preparar_muestra", **completo()).primeras[0].enlace()
    )
    assert "nombre" not in consulta and "responsable_muestreo" not in consulta


def test_tipo_de_vertido_desconocido(empleado, datos):
    resultado = ejecutar(empleado, "preparar_muestra", **completo(tipo_vertido="marciano"))
    salida = resultado.salida
    assert salida["problemas"] == [
        "No reconozco el tipo de vertido «marciano»: elegí Agua, Cloacal o Canal."
    ]
    assert salida["elegir"] == "tipo_vertido"
    assert resultado.primeras == []


def test_sitio_demasiado_largo_lo_rechaza_el_formulario(empleado, datos):
    resultado = ejecutar(empleado, "preparar_muestra", **completo(sitio_extraccion="x" * 201))
    assert resultado.salida["listo"] is False
    assert any("200" in p for p in resultado.salida["problemas"])
    assert resultado.primeras == []


def test_sin_datos_de_contacto(empleado, datos):
    resultado = ejecutar(empleado, "preparar_muestra", **completo())
    todo = json.dumps(resultado.salida, ensure_ascii=False)
    cliente = datos["cliente"]
    for dato in (cliente.email, cliente.telefono, cliente.domicilio, cliente.numero_documento):
        assert dato not in todo


def test_sin_argumentos_falta_todo(empleado, datos):
    resultado = ejecutar(empleado, "preparar_muestra")
    assert resultado.salida["faltan"] == [
        "cliente",
        "origen",
        "tipo de estudio",
        "tipo de vertido",
        "fecha de muestreo",
        "fecha de ingreso",
        "sitio de extracción",
    ]
    assert resultado.avisos == []
    assert resultado.valida is True


def test_usuario_inactivo_no_recibe_enlaces(empleado, datos):
    empleado.is_active = False
    resultado = ejecutar(empleado, "preparar_muestra", **completo())
    assert resultado.primeras == []
    assert resultado.salida["encontrado"] is False


# --- US2 (T020) ---


def test_preparar_estudio_listo(empleado, muestra, datos):
    resultado = ejecutar(
        empleado, "preparar_estudio", numero_pi=muestra.numero_pi, tipo_estudio="bacteriológico"
    )
    salida = resultado.salida
    assert salida["listo"] is True
    assert salida["resuelto"] == {
        "muestra": f"PI {muestra.numero_pi} · Cliente de test · Origen de test",
        "tipo_estudio": "Bacteriológico básico",
    }
    crear, ficha = enlaces(resultado.primeras)
    assert crear["etiqueta"] == "Revisar y crear el estudio"
    assert crear["minimizar"] is True
    ruta, consulta = parametros(crear)
    assert ruta == "/estudios/crear/"
    assert consulta == {"muestra": str(muestra.pk), "tipo": str(datos["bact"].pk)}
    assert ficha == {"etiqueta": f"PI {muestra.numero_pi}", "url": f"/muestras/{muestra.pk}/"}
    assert resultado.avisos == [AVISO_ESTUDIO]
    assert muestra.cliente.email not in json.dumps(salida, ensure_ascii=False)


def test_preparar_estudio_sin_tipo(empleado, muestra, datos):
    resultado = ejecutar(empleado, "preparar_estudio", numero_pi=muestra.numero_pi)
    salida = resultado.salida
    assert salida["faltan"] == ["tipo de estudio"]
    assert salida["elegir"] == "tipo_estudio"
    etiquetas = [o["etiqueta"] for o in enlaces(resultado.opciones)]
    assert etiquetas == ["Bacteriológico básico", "Físico-químico básico"]
    assert resultado.avisos == [f"Hasta ahora: Muestra: PI {muestra.numero_pi}."]


def test_preparar_estudio_sin_muestra(empleado, datos):
    resultado = ejecutar(empleado, "preparar_estudio", tipo_estudio="físico-químico básico")
    assert resultado.salida["faltan"] == ["N° PI de la muestra"]
    assert resultado.primeras == []


# --- US3 (T023) ---


def test_cliente_inexistente(empleado, datos):
    resultado = ejecutar(empleado, "preparar_muestra", **completo(cliente="Acme"))
    salida = resultado.salida
    assert salida["problemas"] == ["No hay ningún cliente activo que coincida con «Acme»."]
    assert salida["listo"] is False
    assert enlaces(resultado.primeras) == [
        {"etiqueta": "Registrar cliente", "url": "/clientes/registrar/"}
    ]
    # Con el cliente sin resolver no se busca el origen.
    assert "origen" not in salida["resuelto"]


def test_cliente_inactivo(empleado, datos):
    from clientes.models import Cliente

    Cliente.objects.filter(pk=datos["cliente"].pk).update(activo=False)
    resultado = ejecutar(empleado, "preparar_muestra", **completo())
    assert resultado.salida["problemas"] == ["El cliente «Lácteos del Sur S.A.» está inactivo."]
    assert resultado.salida["listo"] is False


def test_varios_clientes_para_elegir(empleado, datos):
    from clientes.models import Cliente

    otro = Cliente.objects.create(
        razon_social="Lácteos del Norte", tipo_documento="CUIT", numero_documento="30712345683"
    )
    resultado = ejecutar(empleado, "preparar_muestra", **completo(cliente="Lácteos"))
    salida = resultado.salida
    assert salida["elegir"] == "cliente"
    assert salida["listo"] is False
    opciones = enlaces(resultado.opciones)
    assert opciones == [
        {
            "etiqueta": "Lácteos del Norte",
            "url": f"/clientes/{otro.pk}/",
            "pregunta": "El cliente es Lácteos del Norte",
        },
        {
            "etiqueta": "Lácteos del Sur S.A.",
            "url": f"/clientes/{datos['cliente'].pk}/",
            "pregunta": "El cliente es Lácteos del Sur S.A.",
        },
    ]


def test_nombre_exacto_gana_entre_parecidos(empleado, datos):
    from clientes.models import Cliente

    Cliente.objects.create(
        razon_social="Lácteos del Sur S.A. Planta 2",
        tipo_documento="CUIT",
        numero_documento="30712345691",
    )
    resultado = ejecutar(empleado, "preparar_muestra", **completo(cliente="lacteos del sur s.a."))
    assert resultado.salida["resuelto"]["cliente"] == "Lácteos del Sur S.A."
    assert resultado.salida["elegir"] is None


def test_origen_inexistente_ofrece_los_del_cliente_y_origen_nuevo(empleado, datos):
    resultado = ejecutar(empleado, "preparar_muestra", **completo(origen="pozo 9"))
    salida = resultado.salida
    assert salida["problemas"] == ["«pozo 9» no es un origen de Lácteos del Sur S.A."]
    assert salida["elegir"] == "origen"
    assert enlaces(resultado.opciones) == [
        {"etiqueta": "Pozo 1", "pregunta": "El origen es Pozo 1"},
        {"etiqueta": "Pozo 2", "pregunta": "El origen es Pozo 2"},
        {"etiqueta": "Tanque elevado", "pregunta": "El origen es Tanque elevado"},
        {
            "etiqueta": "Registrarlo como origen nuevo",
            "pregunta": "Registrar «pozo 9» como origen nuevo",
        },
    ]


def test_origen_nuevo_elegido(empleado, datos):
    resultado = ejecutar(
        empleado, "preparar_muestra", **completo(origen="pozo 9", origen_nuevo=True)
    )
    salida = resultado.salida
    assert salida["listo"] is True
    assert salida["resuelto"]["origen"] == "pozo 9 (origen nuevo)"
    _, consulta = parametros(resultado.primeras[0].enlace())
    assert consulta["origen_nuevo"] == "pozo 9"
    assert "origen" not in consulta


def test_origen_nuevo_que_ya_existe_usa_el_existente(empleado, datos):
    resultado = ejecutar(
        empleado, "preparar_muestra", **completo(origen="POZO 2", origen_nuevo=True)
    )
    _, consulta = parametros(resultado.primeras[0].enlace())
    assert consulta["origen"] == str(datos["pozo2"].pk)


def test_varios_origenes_parecidos(empleado, datos):
    resultado = ejecutar(empleado, "preparar_muestra", **completo(origen="pozo"))
    salida = resultado.salida
    assert salida["elegir"] == "origen"
    assert salida["problemas"] == []
    assert [o["etiqueta"] for o in enlaces(resultado.opciones)] == [
        "Pozo 1",
        "Pozo 2",
        "Registrarlo como origen nuevo",
    ]


def test_tipo_inactivo(empleado, datos):
    resultado = ejecutar(empleado, "preparar_muestra", **completo(tipo_estudio="vuelco"))
    salida = resultado.salida
    assert salida["problemas"] == ["El tipo «Vuelco a colectora» no está activo."]
    assert salida["elegir"] == "tipo_estudio"
    assert [o["etiqueta"] for o in enlaces(resultado.opciones)] == [
        "Solo registrar la muestra",
        "Bacteriológico básico",
        "Físico-químico básico",
    ]


def test_tipo_inexistente_ofrece_parecidos(empleado, datos):
    resultado = ejecutar(empleado, "preparar_muestra", **completo(tipo_estudio="químico"))
    salida = resultado.salida
    assert salida["problemas"] == []
    # Una sola coincidencia parcial se usa.
    assert salida["resuelto"]["tipo_estudio"] == "Físico-químico básico"
    resultado = ejecutar(empleado, "preparar_muestra", **completo(tipo_estudio="metales"))
    assert resultado.salida["problemas"] == [
        "No hay ningún tipo de estudio activo que coincida con «metales»."
    ]
    assert resultado.salida["elegir"] == "tipo_estudio"


def test_pi_inexistente(empleado, datos):
    resultado = ejecutar(
        empleado, "preparar_estudio", numero_pi=123456, tipo_estudio="físico-químico básico"
    )
    assert resultado.salida["problemas"] == ["No hay ninguna muestra con el N° PI 123456."]
    assert resultado.opciones == [] and resultado.primeras == []
    assert resultado.salida["listo"] is False


# --- Ajuste de la prueba manual: el modelo manda null en lo que no se dijo ---


def test_argumentos_en_null_son_no_dichos(empleado, datos):
    from asistente import herramientas

    campos = herramientas.REGISTRO["preparar_muestra"].definicion["function"]["parameters"]
    todos_null = {nombre: None for nombre in campos["properties"]}
    resultado = herramientas.ejecutar(empleado, "preparar_muestra", json.dumps(todos_null))
    assert resultado.valida is True
    assert resultado.salida["faltan"][0] == "cliente"
    assert len(resultado.salida["faltan"]) == 7
    con_null = {**completo(), "nombre": None, "origen_nuevo": None, "solo_muestra": None}
    resultado = herramientas.ejecutar(empleado, "preparar_muestra", json.dumps(con_null))
    assert resultado.salida["listo"] is True
    resultado = herramientas.ejecutar(
        empleado, "preparar_estudio", json.dumps({"numero_pi": None, "tipo_estudio": None})
    )
    assert resultado.valida is True
    assert resultado.salida["faltan"] == ["N° PI de la muestra", "tipo de estudio"]


def test_esquemas_admiten_null_y_siguen_validando_tipos(empleado, datos):
    from asistente import herramientas

    for nombre in ("preparar_muestra", "preparar_estudio"):
        propiedades = herramientas.REGISTRO[nombre].definicion["function"]["parameters"][
            "properties"
        ]
        assert all("null" in p["type"] for p in propiedades.values())
    invalida = herramientas.ejecutar(empleado, "preparar_muestra", json.dumps({"cliente": 3}))
    assert invalida.valida is False
    invalida = herramientas.ejecutar(empleado, "preparar_estudio", json.dumps({"numero_pi": True}))
    assert invalida.valida is False


def test_sin_cliente_ni_origen_no_ofrece_tipo_ni_vertido(empleado, datos):
    """Prueba manual: con «quiero registrar una muestra» se pide primero cliente y origen."""
    resultado = ejecutar(empleado, "preparar_muestra")
    assert resultado.salida["elegir"] is None
    assert resultado.opciones == []
    resultado = ejecutar(empleado, "preparar_muestra", cliente="Lácteos del Sur")
    assert resultado.salida["faltan"][0] == "origen"
    assert resultado.salida["elegir"] is None
    resultado = ejecutar(empleado, "preparar_muestra", cliente="Lácteos del Sur", origen="pozo 2")
    assert resultado.salida["elegir"] == "tipo_estudio"
