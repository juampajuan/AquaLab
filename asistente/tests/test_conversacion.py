"""Bucle de conversación (research R3, R8, R9, R11): vueltas, topes, mensaje fijo y enlaces."""

import pytest

from asistente import cliente_ia, conversacion, herramientas
from asistente.enlaces import Referencia

from .conftest import Lenta, herramienta, texto
from .conftest import herramientas as varias

pytestmark = pytest.mark.django_db


@pytest.fixture
def eco(monkeypatch):
    """Herramienta de prueba: devuelve lo que recibe y una referencia a la muestra 7."""
    ejecutadas = []

    def funcion(usuario, valor):
        ejecutadas.append(valor)
        return {"encontrado": True, "datos": {"valor": valor}}, [
            Referencia("muestra", 7, "PI 200417", claves=("PI 200417", "200417"))
        ]

    definicion = {
        "type": "function",
        "function": {
            "name": "eco",
            "description": "Devuelve el valor.",
            "parameters": {
                "type": "object",
                "properties": {"valor": {"type": "string"}},
                "required": ["valor"],
            },
        },
    }
    monkeypatch.setitem(herramientas.REGISTRO, "eco", herramientas.Herramienta(definicion, funcion))
    return ejecutadas


def responder(servicio, pregunta="¿Cómo está el PI 200417?", historial=(), **kwargs):
    return conversacion.responder(None, pregunta, list(historial), reloj=servicio.reloj, **kwargs)


def test_respuesta_sin_herramientas(servicio_simulado):
    """Sin ninguna herramienta, el texto del modelo se descarta (FR-012, research R3)."""
    servicio_simulado.guion(texto("El PI 200417 está Finalizado con pH 7,2."))
    respuesta = responder(servicio_simulado)
    assert respuesta.texto == conversacion.MENSAJE_SOLO_CONSULTA
    assert respuesta.enlaces == []


def test_texto_con_herramienta(servicio_simulado, eco):
    servicio_simulado.guion(
        herramienta("eco", {"valor": "x"}), texto("La muestra PI 200417 está bien.")
    )
    respuesta = responder(servicio_simulado)
    assert respuesta.texto == "La muestra PI 200417 está bien."
    assert eco == ["x"]
    assert respuesta.enlaces == [{"etiqueta": "PI 200417", "url": "/muestras/7/"}]


def test_solo_herramientas_invalidas(servicio_simulado, eco):
    servicio_simulado.guion(
        herramienta("desconocida", {}),
        herramienta("eco", {"otro": 1}),
        texto("El PI 200417 tiene pH 7,2."),
    )
    respuesta = responder(servicio_simulado)
    assert respuesta.texto == conversacion.MENSAJE_SOLO_CONSULTA
    assert eco == []


def test_mensajes_enviados(servicio_simulado):
    servicio_simulado.guion(texto("Hola"))
    historial = [
        {"rol": "usuario", "texto": "¿Cómo está el PI 200417?"},
        {"rol": "asistente", "texto": "La muestra PI 200417 …"},
    ]
    responder(servicio_simulado, "¿y qué no cumple?", historial)
    [llamada] = servicio_simulado.llamadas
    mensajes = llamada["mensajes"]
    assert mensajes[0] == {"role": "system", "content": conversacion.MENSAJE_SISTEMA}
    assert mensajes[1:] == [
        {"role": "user", "content": "¿Cómo está el PI 200417?"},
        {"role": "assistant", "content": "La muestra PI 200417 …"},
        {"role": "user", "content": "¿y qué no cumple?"},
    ]
    assert llamada["herramientas"] == herramientas.definiciones()


def test_resultado_de_herramienta_en_mensajes(servicio_simulado, eco):
    servicio_simulado.guion(herramienta("eco", {"valor": "x"}, id_="a"), texto("Listo PI 200417"))
    responder(servicio_simulado)
    segunda = servicio_simulado.llamadas[1]["mensajes"]
    assert segunda[-2]["role"] == "assistant"
    assert segunda[-2]["tool_calls"][0]["function"]["name"] == "eco"
    assert segunda[-1]["role"] == "tool"
    assert segunda[-1]["tool_call_id"] == "a-0"
    assert '"valor": "x"' in segunda[-1]["content"]


def test_tope_vueltas(servicio_simulado, eco):
    """7 pedidos de herramientas: se ejecutan 6 y se responde 200 con el mensaje de tope."""
    servicio_simulado.guion(*[herramienta("eco", {"valor": str(i)}) for i in range(7)])
    respuesta = responder(servicio_simulado)
    assert respuesta.texto == conversacion.MENSAJE_TOPE
    assert respuesta.enlaces == []
    assert len(eco) == 6


def test_tope_ejecuciones(servicio_simulado, eco, settings):
    from asistente import configuracion

    config = configuracion.Configuracion(clave="c", url="u", modelo="m", max_vueltas=20)
    servicio_simulado.guion(*[herramienta("eco", {"valor": str(i)}) for i in range(9)])
    respuesta = responder(servicio_simulado, config=config)
    assert respuesta.texto == conversacion.MENSAJE_TOPE
    assert len(eco) == 8


def test_una_herramienta_por_vuelta(servicio_simulado, eco):
    servicio_simulado.guion(
        varias([("eco", {"valor": "uno"}), ("eco", {"valor": "dos"})], id_="v"),
        texto("PI 200417 listo"),
    )
    responder(servicio_simulado)
    assert eco == ["uno"]
    mensajes = servicio_simulado.llamadas[1]["mensajes"]
    respuestas_tool = [m for m in mensajes if m["role"] == "tool"]
    assert [m["tool_call_id"] for m in respuestas_tool] == ["v-0", "v-1"]
    assert conversacion.MENSAJE_UNA_POR_VUELTA in respuestas_tool[1]["content"]


def test_una_por_vuelta_no_cuenta_ejecuciones(servicio_simulado, eco):
    from asistente import configuracion

    config = configuracion.Configuracion(clave="c", url="u", modelo="m", max_vueltas=20)
    pedidos = [varias([("eco", {"valor": str(i)}), ("eco", {"valor": "extra"})]) for i in range(8)]
    servicio_simulado.guion(*pedidos, texto("PI 200417"))
    respuesta = responder(servicio_simulado, config=config)
    assert respuesta.texto == "PI 200417"
    assert len(eco) == 8


def test_presupuesto(servicio_simulado, eco):
    """Cada llamada recibe min(15, lo que queda de 20)."""
    servicio_simulado.guion(
        Lenta(8, herramienta("eco", {"valor": "x"})),
        Lenta(6, herramienta("eco", {"valor": "y"})),
        texto("PI 200417"),
    )
    responder(servicio_simulado)
    assert [ll["timeout"] for ll in servicio_simulado.llamadas] == [15, 12, 6]


def test_segunda_llamada_lenta(servicio_simulado, eco):
    """La segunda llamada vence su timeout recortado: no disponible, sin tercera (SC-007)."""
    servicio_simulado.guion(
        Lenta(8, herramienta("eco", {"valor": "x"})),
        Lenta(30, texto("tarde")),
        texto("nunca"),
    )
    with pytest.raises(cliente_ia.ServicioNoDisponible):
        responder(servicio_simulado)
    assert len(servicio_simulado.llamadas) == 2
    assert servicio_simulado.llamadas[1]["timeout"] == 12
    assert servicio_simulado.reloj.ahora <= 20


def test_sin_tiempo_restante(servicio_simulado, eco):
    servicio_simulado.guion(Lenta(14, herramienta("eco", {"valor": "x"})), texto("PI 200417"))
    servicio_simulado.reloj.ahora = 0

    def eco_lento(usuario, valor):
        servicio_simulado.reloj.ahora += 10
        return {"encontrado": True}, []

    herramientas.REGISTRO["eco"] = herramientas.Herramienta(
        herramientas.REGISTRO["eco"].definicion, eco_lento
    )
    with pytest.raises(cliente_ia.ServicioNoDisponible):
        responder(servicio_simulado)
    assert len(servicio_simulado.llamadas) == 1


def test_herramienta_desconocida(servicio_simulado):
    servicio_simulado.guion(herramienta("borrar_todo", {}), texto("Hecho"))
    responder(servicio_simulado)
    contenido = servicio_simulado.llamadas[1]["mensajes"][-1]["content"]
    assert "Pedido inválido." in contenido


@pytest.mark.parametrize("argumentos", ["{no es json", '"texto"', '{"valor": 3}', "{}"])
def test_argumentos_invalidos(servicio_simulado, eco, argumentos):
    servicio_simulado.guion(herramienta("eco", argumentos), texto("Hecho"))
    responder(servicio_simulado)
    assert eco == []
    assert "Pedido inválido." in servicio_simulado.llamadas[1]["mensajes"][-1]["content"]


def test_url_del_modelo_no_es_enlace(servicio_simulado, eco):
    servicio_simulado.guion(
        herramienta("eco", {"valor": "x"}), texto("Mirá http://malo.test/x y el PI 200417")
    )
    respuesta = responder(servicio_simulado)
    assert "http://malo.test/x" in respuesta.texto
    assert [e["url"] for e in respuesta.enlaces] == ["/muestras/7/"]


# --- US1: preguntar por una muestra ---


def test_pregunta_por_pi(empleado, estudio_completo, muestra, servicio_simulado):
    """US1 Esc. 3: una herramienta por vuelta y enlaces a la muestra y al estudio."""
    servicio_simulado.guion(
        herramienta("buscar_muestra", {"numero_pi": 200001}),
        herramienta("detalle_estudio", {"numero": estudio_completo.pk}),
        texto(f"La muestra PI 200001 tiene el Estudio {estudio_completo.pk} En proceso."),
    )
    respuesta = conversacion.responder(
        empleado, "¿Cómo está el PI 200001?", [], reloj=servicio_simulado.reloj
    )
    assert respuesta.enlaces == [
        {"etiqueta": "PI 200001", "url": f"/muestras/{muestra.pk}/"},
        {"etiqueta": f"Estudio {estudio_completo.pk}", "url": f"/estudios/{estudio_completo.pk}/"},
    ]
    nombres = [ll["mensajes"][-1].get("content") for ll in servicio_simulado.llamadas[1:]]
    assert '"numero_pi": 200001' in nombres[0]
    assert '"pruebas"' in nombres[1]


def test_enlaces_sin_mencion(empleado, estudio_completo, muestra, cliente_a, servicio_simulado):
    servicio_simulado.guion(
        herramienta("buscar_muestra", {"numero_pi": 200001}), texto("Está en proceso.")
    )
    respuesta = conversacion.responder(empleado, "¿Y?", [], reloj=servicio_simulado.reloj)
    assert [e["url"] for e in respuesta.enlaces] == [
        f"/muestras/{muestra.pk}/",
        f"/estudios/{estudio_completo.pk}/",
        f"/clientes/{cliente_a.pk}/",
    ]


def test_sin_herramientas_mensaje_fijo(servicio_simulado):
    """El modelo responde de memoria con un valor inventado: no llega al usuario (FR-004)."""
    servicio_simulado.guion(texto("El PI 200001 tiene pH 9,9."))
    respuesta = conversacion.responder(None, "¿pH?", [], reloj=servicio_simulado.reloj)
    assert respuesta.texto == conversacion.MENSAJE_SOLO_CONSULTA
    assert "9,9" not in respuesta.texto
    assert respuesta.enlaces == []


def test_muestra_con_muchos_estudios(empleado, muestra, catalogo, servicio_simulado):
    """US1 Esc. 7 / FR-009a: el aviso y el enlace a la ficha los pone AquaLab."""
    import uuid

    from estudios.models import TipoEstudio
    from estudios.servicios import crear_estudio
    from pruebas.models import Prueba

    tipo = TipoEstudio.objects.create(nombre="Muchos")
    tipo.pruebas.set(Prueba.objects.filter(codigo="PH"))
    estudios = [
        crear_estudio(
            {
                "clave": str(uuid.uuid4()),
                "muestra": muestra.pk,
                "tipo": tipo.pk,
                "version": tipo.version,
            },
            empleado,
        )
        for _ in range(7)
    ]
    servicio_simulado.guion(
        herramienta("buscar_muestra", {"numero_pi": 200001}),
        texto(f"El Estudio {estudios[-1].pk} está Sin iniciar."),
    )
    respuesta = conversacion.responder(empleado, "¿PI 200001?", [], reloj=servicio_simulado.reloj)
    assert respuesta.texto.endswith(
        "La muestra PI 200001 tiene 7 estudios; se detallan los 5 más recientes. "
        "El resto está en la ficha de la muestra."
    )
    assert respuesta.enlaces[0] == {"etiqueta": "PI 200001", "url": f"/muestras/{muestra.pk}/"}


# --- US2: qué no cumple ---


def test_que_no_cumple(empleado, escuela, servicio_simulado):
    """Buscar el estudio por texto, elegir el viejo y pedir solo lo fuera de norma."""
    viejo = escuela["viejo"]
    servicio_simulado.guion(
        herramienta("detalle_estudio", {"texto": "escuela técnica"}),
        herramienta("detalle_estudio", {"numero": viejo.pk, "solo_fuera_de_norma": True}),
        texto(f"En el Estudio {viejo.pk} no cumple el Cloruro: 400 mg/l (máx. 350.0)."),
    )
    respuesta = conversacion.responder(
        empleado, "¿Qué no cumple en la escuela técnica?", [], reloj=servicio_simulado.reloj
    )
    assert respuesta.enlaces[0] == {
        "etiqueta": f"Estudio {viejo.pk}",
        "url": f"/estudios/{viejo.pk}/",
    }
    ultima = servicio_simulado.llamadas[2]["mensajes"][-1]["content"]
    assert '"codigo": "CL-"' in ultima
    assert '"codigo": "PH"' not in ultima


def test_varias_coincidencias_enlaces(empleado, escuela, servicio_simulado):
    nuevo, viejo = escuela["nuevo"], escuela["viejo"]
    servicio_simulado.guion(
        herramienta("detalle_estudio", {"texto": "escuela"}),
        texto(f"Hay dos estudios: el Estudio {nuevo.pk} y el Estudio {viejo.pk}. ¿Cuál?"),
    )
    respuesta = conversacion.responder(
        empleado, "¿Qué no cumple?", [], reloj=servicio_simulado.reloj
    )
    assert [e["url"] for e in respuesta.enlaces] == [
        f"/estudios/{nuevo.pk}/",
        f"/estudios/{viejo.pk}/",
    ]
