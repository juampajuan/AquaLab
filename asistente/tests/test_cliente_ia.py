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


# --- Traducción de errores (US4, contracts/servicio-ia.md) ---


def error_http(codigo):
    return urllib.error.HTTPError("https://ia.test", codigo, "error", {}, io.BytesIO(b"{}"))


def test_429_cuota_agotada(capturar, caplog):
    capturar(error_http(429))
    with pytest.raises(cliente_ia.CuotaAgotada) as error:
        cliente_ia.enviar([], HERRAMIENTAS, timeout=5)
    assert error.value.motivo == "cuota agotada"
    assert "cuota agotada" in caplog.text


@pytest.mark.parametrize("codigo", [401, 403])
def test_clave_invalida(capturar, caplog, codigo):
    capturar(error_http(codigo))
    with pytest.raises(cliente_ia.ServicioNoDisponible) as error:
        cliente_ia.enviar([], HERRAMIENTAS, timeout=5)
    assert not isinstance(error.value, cliente_ia.CuotaAgotada)
    assert error.value.motivo == "clave inválida o sin acceso (401/403)"
    assert "clave inválida o sin acceso (401/403)" in caplog.text


@pytest.mark.parametrize("codigo", [400, 404, 500, 502, 503])
def test_otros_errores_http(capturar, caplog, codigo):
    capturar(error_http(codigo))
    with pytest.raises(cliente_ia.ServicioNoDisponible) as error:
        cliente_ia.enviar([], HERRAMIENTAS, timeout=5)
    assert error.value.motivo == f"error HTTP {codigo}"
    assert f"error HTTP {codigo}" in caplog.text


@pytest.mark.parametrize(
    "falla",
    [TimeoutError("lento"), TimeoutError("lento"), urllib.error.URLError("sin red")],
)
def test_sin_respuesta(capturar, caplog, falla):
    capturar(falla)
    with pytest.raises(cliente_ia.ServicioNoDisponible) as error:
        cliente_ia.enviar([], HERRAMIENTAS, timeout=5)
    assert error.value.motivo == "sin respuesta"
    assert "sin respuesta" in caplog.text


def test_cuerpo_no_json(monkeypatch, config_asistente, caplog):
    monkeypatch.setattr(
        urllib.request, "urlopen", lambda pedido, timeout=None: RespuestaHttp(b"<html>")
    )
    with pytest.raises(cliente_ia.ServicioNoDisponible) as error:
        cliente_ia.enviar([], HERRAMIENTAS, timeout=5)
    assert error.value.motivo == "respuesta inválida"
    assert "respuesta inválida" in caplog.text


@pytest.mark.parametrize("cuerpo", [{"sin": "choices"}, {"choices": []}, {"choices": [{}]}])
def test_sin_choices_respuesta_invalida(capturar, cuerpo):
    capturar(cuerpo)
    with pytest.raises(cliente_ia.ServicioNoDisponible) as error:
        cliente_ia.enviar([], HERRAMIENTAS, timeout=5)
    assert error.value.motivo == "respuesta inválida"


@pytest.mark.parametrize("falla", [error_http(429), error_http(401), TimeoutError("x")])
def test_log_sin_datos_del_pedido(capturar, caplog, falla):
    capturar(falla)
    mensajes = [{"role": "user", "content": "¿Cómo está el PI 200417 de Lácteos del Sur?"}]
    with pytest.raises(cliente_ia.ErrorServicio):
        cliente_ia.enviar(mensajes, HERRAMIENTAS, timeout=5)
    for prohibido in ("clave-test", "200417", "Lácteos", "buscar_muestra"):
        assert prohibido not in caplog.text


# --- Retry-After del 429 (reintento automático) ---


def error_429(retry_after=None):
    cabeceras = {} if retry_after is None else {"Retry-After": retry_after}
    return urllib.error.HTTPError("https://ia.test", 429, "error", cabeceras, io.BytesIO(b"{}"))


@pytest.mark.parametrize(
    "retry_after, segundos",
    [
        ("2", 2.0),
        ("0.5", 0.5),
        (" 3 ", 3.0),
        (None, None),
        ("pronto", None),
        ("-1", None),
        ("Wed, 21 Oct 2026 07:28:00 GMT", None),
    ],
)
def test_429_lee_retry_after(capturar, retry_after, segundos):
    """El 429 informa en cuántos segundos reintentar (solo la forma en segundos)."""
    capturar(error_429(retry_after))
    with pytest.raises(cliente_ia.CuotaAgotada) as error:
        cliente_ia.enviar([], HERRAMIENTAS, timeout=5)
    assert error.value.reintentar_en == segundos
