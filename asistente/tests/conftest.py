"""Fixtures del asistente (US 10.1). Ningún test llama al servicio de IA (research R1)."""

import json
import urllib.request

import pytest

from asistente import cliente_ia
from estudios.tests.conftest import *  # noqa: F401,F403


@pytest.fixture(autouse=True)
def sin_red(monkeypatch):
    """Hace fallar cualquier `urlopen` que un test no haya simulado."""

    def prohibido(*args, **kwargs):
        raise AssertionError("Un test intentó llamar al servicio de IA")

    monkeypatch.setattr(urllib.request, "urlopen", prohibido)


@pytest.fixture
def config_asistente(settings):
    settings.ASISTENTE = {
        "clave": "clave-test",
        "url": "https://ia.test/v1/chat/completions",
        "modelo": "modelo-test",
    }
    return settings.ASISTENTE


def texto(contenido):
    """Respuesta guionada del modelo: un texto final."""
    return {"role": "assistant", "content": contenido}


def herramienta(nombre, argumentos=None, id_="llamada-1"):
    """Respuesta guionada del modelo: pide una herramienta."""
    return herramientas([(nombre, argumentos or {})], id_)


def herramientas(pedidos, id_="llamada"):
    """Respuesta guionada del modelo: pide varias herramientas en la misma vuelta."""
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": f"{id_}-{i}",
                "type": "function",
                "function": {
                    "name": nombre,
                    "arguments": argumentos
                    if isinstance(argumentos, str)
                    else json.dumps(argumentos),
                },
            }
            for i, (nombre, argumentos) in enumerate(pedidos)
        ],
    }


class Lenta:
    """Una respuesta que tarda `segundos`: si supera el timeout recibido, vence."""

    def __init__(self, segundos, respuesta):
        self.segundos = segundos
        self.respuesta = respuesta


class Reloj:
    def __init__(self):
        self.ahora = 0.0

    def __call__(self):
        return self.ahora


class ServicioSimulado:
    """Reemplaza `cliente_ia.enviar` con una cola de respuestas guionadas."""

    def __init__(self):
        self.respuestas = []
        self.llamadas = []
        self.reloj = Reloj()

    def guion(self, *respuestas):
        self.respuestas.extend(respuestas)

    def __call__(self, mensajes, herramientas, timeout, config=None):
        self.llamadas.append(
            {
                "mensajes": json.loads(json.dumps(mensajes)),
                "herramientas": herramientas,
                "timeout": timeout,
            }
        )
        if not self.respuestas:
            raise AssertionError("El servicio simulado no tiene más respuestas")
        respuesta = self.respuestas.pop(0)
        if isinstance(respuesta, Lenta):
            if respuesta.segundos >= timeout:
                self.reloj.ahora += timeout
                raise cliente_ia.ServicioNoDisponible("sin respuesta")
            self.reloj.ahora += respuesta.segundos
            respuesta = respuesta.respuesta
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta


@pytest.fixture
def servicio_simulado(monkeypatch, config_asistente):
    servicio = ServicioSimulado()
    monkeypatch.setattr(cliente_ia, "enviar", servicio)
    return servicio
