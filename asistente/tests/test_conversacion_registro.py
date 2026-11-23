"""Pedidos de registro en la conversación (US 10.3, research R1, R2, R10)."""

import json

import pytest

from asistente import conversacion

from .conftest import herramienta, texto

pytestmark = pytest.mark.django_db


# --- Corte por verbos (T004) ---


@pytest.mark.parametrize(
    "pregunta",
    [
        "Registrá una muestra de Lácteos del Sur, pozo 2, para un físico-químico básico",
        "Creá un estudio para el PI 200417",
        "cargá una muestra de la escuela",
        "Por favor, registrá un estudio bacteriológico para el PI 200417",
        "Registrá otra muestra de Lácteos del Sur",
        "Creá un nuevo estudio para el PI 200417",
        "¿Registrá la muestra de Lácteos?",
    ],
)
def test_pedidos_de_registro_llegan_al_servicio(servicio_simulado, pregunta):
    servicio_simulado.guion(herramienta("preparar_muestra", {}), texto("¿De qué cliente?"))
    conversacion.responder(None, pregunta, [], reloj=servicio_simulado.reloj)
    assert len(servicio_simulado.llamadas) == 2


@pytest.mark.parametrize(
    "pregunta",
    [
        "Validá el estudio 42",
        "Borrá la muestra 200045",
        "Cargá el pH",
        "Cargá las mediciones del estudio 42",
        "Agregá una prueba al estudio 42",
        "Creá un informe del estudio 42",
        "Registrá la validación del estudio 42",
    ],
)
def test_otros_cambios_siguen_cortados(servicio_simulado, pregunta):
    respuesta = conversacion.responder(None, pregunta, [], reloj=servicio_simulado.reloj)
    assert respuesta.texto == conversacion.MENSAJE_SOLO_CONSULTA
    assert respuesta.enlaces == conversacion.solo_consulta().enlaces
    assert servicio_simulado.llamadas == []


@pytest.mark.parametrize(
    "pregunta", ["Registrá el cliente Juan Pérez", "Por favor, creá un cliente nuevo"]
)
def test_alta_de_cliente_mensaje_fijo(servicio_simulado, pregunta):
    respuesta = conversacion.responder(None, pregunta, [], reloj=servicio_simulado.reloj)
    assert respuesta.texto == conversacion.MENSAJE_ALTA_CLIENTE
    assert respuesta.enlaces == [{"etiqueta": "Registrar cliente", "url": "/clientes/registrar/"}]
    assert servicio_simulado.llamadas == []


def test_mensaje_de_sistema_explica_el_registro():
    sistema = conversacion.MENSAJE_SISTEMA
    assert "preparar_muestra" in sistema
    assert "preparar_estudio" in sistema
    assert "las dos fechas juntas" in sistema
    assert "confirma en el formulario" in sistema


# --- Guiones completos (T013, T021) ---


@pytest.fixture
def lacteos_registro():
    from clientes.models import Cliente
    from estudios.models import TipoEstudio
    from muestras.models import Origen

    cliente = Cliente.objects.create(
        razon_social="Lácteos del Sur S.A.",
        tipo_documento="CUIT",
        numero_documento="30712345675",
        email="contacto@lacteos.test",
    )
    return {
        "cliente": cliente,
        "pozo2": Origen.objects.create(cliente=cliente, nombre="Pozo 2"),
        "fq": TipoEstudio.objects.create(nombre="Físico-químico básico"),
        "bact": TipoEstudio.objects.create(nombre="Bacteriológico básico"),
    }


PEDIDO = "Registrá una muestra de Lácteos del Sur, pozo 2, para un físico-químico básico"
DICHO = {"cliente": "Lácteos del Sur", "origen": "pozo 2", "tipo_estudio": "físico-químico básico"}


def preguntar(servicio, usuario, pregunta, historial):
    respuesta = conversacion.responder(usuario, pregunta, historial, reloj=servicio.reloj)
    historial += [
        {"rol": "usuario", "texto": pregunta},
        {"rol": "asistente", "texto": respuesta.texto},
    ]
    return respuesta


def test_ejemplo_de_la_historia_en_tres_mensajes(empleado, lacteos_registro, servicio_simulado):
    historial = []
    servicio_simulado.guion(
        herramienta("preparar_muestra", DICHO), texto("¿Qué tipo de vertido es?")
    )
    primera = preguntar(servicio_simulado, empleado, PEDIDO, historial)
    assert primera.texto.startswith("¿Qué tipo de vertido")
    assert primera.texto.endswith(
        "Hasta ahora: Cliente: Lácteos del Sur S.A. · Origen: Pozo 2 · Tipo de estudio: "
        "Físico-químico básico."
    )
    assert [e["etiqueta"] for e in primera.enlaces] == ["Agua", "Cloacal", "Canal"]

    con_vertido = {**DICHO, "tipo_vertido": "Agua"}
    servicio_simulado.guion(
        herramienta("preparar_muestra", con_vertido),
        texto("¿Cuándo se tomó, cuándo llegó y de qué punto exacto se extrajo?"),
    )
    segunda = preguntar(servicio_simulado, empleado, primera.enlaces[0]["pregunta"], historial)
    assert not any(e.get("minimizar") for e in segunda.enlaces)
    assert "Vertido: Agua" in segunda.texto

    servicio_simulado.guion(
        herramienta(
            "preparar_muestra",
            {
                **con_vertido,
                "fecha_muestreo": "ayer",
                "fecha_ingreso": "hoy",
                "sitio_extraccion": "boca del pozo",
                "nombre": "Pozo 2 – Control de noviembre",
            },
        ),
        texto("Listo: revisá los datos y confirmá el registro."),
    )
    tercera = preguntar(
        servicio_simulado, empleado, "la tomaron ayer de la boca del pozo, llegó hoy", historial
    )
    assert tercera.enlaces[0]["etiqueta"] == "Revisar y registrar la muestra"
    assert tercera.enlaces[0]["minimizar"] is True
    assert tercera.enlaces[0]["url"].startswith("/muestras/registrar/?cliente=")
    assert "sitio_extraccion=boca+del+pozo" in tercera.enlaces[0]["url"]
    assert "tipo_vertido=agua" in tercera.enlaces[0]["url"]
    assert tercera.texto.endswith(
        "La muestra se registra recién cuando confirmes en el formulario."
    )
    # El historial que mandó el navegador llegó al servicio.
    enviados = servicio_simulado.llamadas[4]["mensajes"]
    assert enviados[1]["content"] == PEDIDO


def test_sin_tipo_una_eleccion_mas(empleado, lacteos_registro, servicio_simulado):
    """SC-001: cada elección que haga falta suma un mensaje (acá, el tipo de estudio)."""
    historial = []
    sin_tipo = {"cliente": "Lácteos del Sur", "origen": "pozo 2", "tipo_vertido": "cloacal"}
    servicio_simulado.guion(
        herramienta("preparar_muestra", sin_tipo), texto("¿Qué tipo de estudio?")
    )
    primera = preguntar(
        servicio_simulado, empleado, "Registrá una muestra de Lácteos del Sur, pozo 2", historial
    )
    assert primera.enlaces[0]["pregunta"] == "Solo registrar la muestra, sin estudio"

    servicio_simulado.guion(
        herramienta("preparar_muestra", {**sin_tipo, "solo_muestra": True}),
        texto("¿Cuándo se tomó y cuándo llegó?"),
    )
    preguntar(servicio_simulado, empleado, primera.enlaces[0]["pregunta"], historial)

    servicio_simulado.guion(
        herramienta(
            "preparar_muestra",
            {
                **sin_tipo,
                "solo_muestra": True,
                "fecha_muestreo": "hoy",
                "fecha_ingreso": "hoy",
                "sitio_extraccion": "canilla",
                "nombre": "Pozo 2 – Control de noviembre",
            },
        ),
        texto("Listo."),
    )
    tercera = preguntar(servicio_simulado, empleado, "las dos hoy, de la canilla", historial)
    assert tercera.enlaces[0]["etiqueta"] == "Revisar y registrar la muestra"
    assert "tipo_estudio" not in tercera.enlaces[0]["url"]
    assert len([m for m in historial if m["rol"] == "usuario"]) == 3


def test_conversacion_larga_sobrevive_con_el_resumen(empleado, lacteos_registro, servicio_simulado):
    """R10: el pedido original ya salió del historial, pero el último resumen sigue."""
    resumen = (
        "Hasta ahora: Cliente: Lácteos del Sur S.A. · Origen: Pozo 2 · Tipo de estudio: "
        "Físico-químico básico · Vertido: Agua · Sitio: Boca del pozo."
    )
    historial = [
        {"rol": "usuario", "texto": "el 12/13"},
        {"rol": "asistente", "texto": f"No entendí la fecha de muestreo.\n\n{resumen}"},
        {"rol": "usuario", "texto": "perdón, el 12/11"},
        {"rol": "asistente", "texto": f"¿Y la de ingreso?\n\n{resumen}"},
        {"rol": "usuario", "texto": "¿cómo la escribo?"},
        {"rol": "asistente", "texto": f"Por ejemplo «hoy» o «13/11».\n\n{resumen}"},
    ]
    servicio_simulado.guion(
        herramienta(
            "preparar_muestra",
            {
                "cliente": "Lácteos del Sur S.A.",
                "origen": "Pozo 2",
                "tipo_estudio": "Físico-químico básico",
                "tipo_vertido": "Agua",
                "sitio_extraccion": "Boca del pozo",
                "nombre": "Pozo 2 – Control de noviembre",
                "fecha_muestreo": "12/11",
                "fecha_ingreso": "hoy",
            },
        ),
        texto("Listo."),
    )
    respuesta = conversacion.responder(empleado, "hoy", historial, reloj=servicio_simulado.reloj)
    assert respuesta.enlaces[0]["etiqueta"] == "Revisar y registrar la muestra"
    enviados = json.dumps(servicio_simulado.llamadas[0]["mensajes"], ensure_ascii=False)
    assert resumen in enviados


def test_estudio_para_muestra_existente(
    empleado, muestra, lacteos_registro, servicio_simulado, cliente_http
):
    from estudios.models import Estudio

    servicio_simulado.guion(
        herramienta(
            "preparar_estudio", {"numero_pi": muestra.numero_pi, "tipo_estudio": "bacteriológico"}
        ),
        texto("Revisá y confirmá el estudio."),
    )
    respuesta = conversacion.responder(
        empleado,
        f"Creá un estudio bacteriológico para el PI {muestra.numero_pi}",
        [],
        reloj=servicio_simulado.reloj,
    )
    assert respuesta.enlaces[0]["etiqueta"] == "Revisar y crear el estudio"
    assert not Estudio.objects.exists()
    # Seguir el enlace: la pantalla de siempre, con muestra y tipo elegidos y sin crear nada.
    html = cliente_http.get(respuesta.enlaces[0]["url"]).content.decode()
    bact = lacteos_registro["bact"]
    assert f'<option value="{muestra.pk}" selected>' in html
    assert f'<option value="{bact.pk}" selected>' in html
    assert not Estudio.objects.exists()
