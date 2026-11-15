"""Llamada al servicio de IA (contracts/servicio-ia.md). `enviar` es el único punto de red: los
tests la parchean y `asistente/tests/conftest.py` bloquea cualquier `urlopen` no simulado."""

import json
import logging
import urllib.error
import urllib.request

from . import configuracion

logger = logging.getLogger("asistente")


class ErrorServicio(Exception):
    """Falla del servicio de IA. `motivo` es lo único que se registra (nunca datos del pedido)."""

    def __init__(self, motivo):
        super().__init__(motivo)
        self.motivo = motivo


class ServicioNoDisponible(ErrorServicio):
    pass


class CuotaAgotada(ErrorServicio):
    pass


def enviar(mensajes, herramientas, timeout, config=None):
    """Manda la conversación y devuelve `choices[0].message` del servicio."""
    config = config or configuracion.actual()
    cuerpo = {"model": config.modelo, "temperature": 0, "messages": mensajes}
    if herramientas:
        # Una herramienta por vuelta (research R11): no se depende de llamadas en paralelo.
        cuerpo.update(tools=herramientas, tool_choice="auto", parallel_tool_calls=False)
    pedido = urllib.request.Request(
        config.url,
        data=json.dumps(cuerpo).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {config.clave}",
            "Content-Type": "application/json",
            "User-Agent": "AquaLab",
        },
    )
    try:
        with urllib.request.urlopen(pedido, timeout=timeout) as respuesta:
            cuerpo_respuesta = respuesta.read()
    except urllib.error.HTTPError as error:
        raise falla(error_http(error.code)) from error
    except OSError as error:
        # URLError, TimeoutError y socket.timeout son OSError.
        raise falla(ServicioNoDisponible("sin respuesta")) from error
    try:
        return json.loads(cuerpo_respuesta.decode("utf-8"))["choices"][0]["message"]
    except (ValueError, KeyError, IndexError, TypeError, AttributeError) as error:
        raise falla(ServicioNoDisponible("respuesta inválida")) from error


def error_http(codigo):
    """Traduce el código HTTP del servicio (contracts/servicio-ia.md)."""
    if codigo == 429:
        return CuotaAgotada("cuota agotada")
    if codigo in (401, 403):
        # Para el usuario es «no disponible»; el log le dice a quien administra que es la clave.
        return ServicioNoDisponible("clave inválida o sin acceso (401/403)")
    return ServicioNoDisponible(f"error HTTP {codigo}")


def falla(error):
    """Registra el motivo (nunca la clave, la pregunta ni los datos enviados) y lo devuelve."""
    logger.warning("Asistente: %s.", error.motivo)
    return error
