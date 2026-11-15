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
            datos = json.loads(respuesta.read().decode("utf-8"))
        return datos["choices"][0]["message"]
    except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
        # OSError incluye URLError, HTTPError y los timeouts. La traducción por código HTTP
        # (cuota, clave inválida) se completa en la US4 del asistente (T046).
        logger.warning("Asistente: el servicio no respondió (%s).", type(error).__name__)
        raise ServicioNoDisponible("sin respuesta") from error
