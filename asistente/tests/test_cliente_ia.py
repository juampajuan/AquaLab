"""Llamada al servicio de IA con urllib (contracts/servicio-ia.md). Único archivo que simula
`urlopen`; los demás tests parchean `cliente_ia.enviar`."""

import io
import json
import urllib.error
import urllib.request

import pytest

from asistente import cliente_ia


class RespuestaHttp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


@pytest.fixture
def capturar(monkeypatch, config_asistente):
    pedidos = []

    def responder(cuerpo):
        def urlopen(pedido, timeout=None):
            pedidos.append((pedido, timeout))
            if isinstance(cuerpo, Exception):
                raise cuerpo
            return RespuestaHttp(json.dumps(cuerpo).encode())

        monkeypatch.setattr(urllib.request, "urlopen", urlopen)
        return pedidos

    return responder


RESPUESTA_OK = {"choices": [{"message": {"role": "assistant", "content": "Hola"}}]}
HERRAMIENTAS = [{"type": "function", "function": {"name": "buscar_muestra", "parameters": {}}}]


def test_pedido(capturar):
    pedidos = capturar(RESPUESTA_OK)
    mensajes = [{"role": "user", "content": "¿Cómo está el PI 200417?"}]
    mensaje = cliente_ia.enviar(mensajes, HERRAMIENTAS, timeout=12)
    assert mensaje == {"role": "assistant", "content": "Hola"}
    [(pedido, timeout)] = pedidos
    assert timeout == 12
    assert pedido.full_url == "https://ia.test/v1/chat/completions"
    assert pedido.get_method() == "POST"
    assert pedido.get_header("Authorization") == "Bearer clave-test"
    assert pedido.get_header("Content-type") == "application/json"
    assert pedido.get_header("User-agent") == "AquaLab"
    cuerpo = json.loads(pedido.data)
    assert cuerpo == {
        "model": "modelo-test",
        "temperature": 0,
        "messages": mensajes,
        "tools": HERRAMIENTAS,
        "tool_choice": "auto",
        "parallel_tool_calls": False,
    }


def test_sin_herramientas_no_manda_tools(capturar):
    pedidos = capturar(RESPUESTA_OK)
    cliente_ia.enviar([{"role": "user", "content": "hola"}], [], timeout=5)
    cuerpo = json.loads(pedidos[0][0].data)
    assert "tools" not in cuerpo
    assert "tool_choice" not in cuerpo
    assert "parallel_tool_calls" not in cuerpo


@pytest.mark.parametrize(
    "falla",
    [
        TimeoutError("lento"),
        urllib.error.URLError("sin red"),
        urllib.error.HTTPError("https://ia.test", 500, "error", {}, None),
    ],
)
def test_falla_de_red_no_disponible(capturar, falla):
    capturar(falla)
    with pytest.raises(cliente_ia.ServicioNoDisponible):
        cliente_ia.enviar([], HERRAMIENTAS, timeout=5)


@pytest.mark.parametrize("cuerpo", [{"sin": "choices"}, {"choices": []}])
def test_respuesta_invalida(capturar, cuerpo):
    capturar(cuerpo)
    with pytest.raises(cliente_ia.ServicioNoDisponible):
        cliente_ia.enviar([], HERRAMIENTAS, timeout=5)
