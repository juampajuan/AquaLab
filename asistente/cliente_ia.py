"""Llamada al servicio de IA (contracts/servicio-ia.md). `enviar` es el único punto de red: los
tests la parchean y `asistente/tests/conftest.py` bloquea cualquier `urlopen` no simulado."""

import json
import logging
import math
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
    """429. `reintentar_en`: los segundos del Retry-After del servicio, o None si no vino o no es
    un número de segundos (la conversación decide si reintenta, research R10)."""

    def __init__(self, motivo, reintentar_en=None):
        super().__init__(motivo)
        self.reintentar_en = reintentar_en


# Palabras que delatan el razonamiento interno del modelo cuando se cuela en la respuesta (los
# modelos gpt-oss a veces lo escriben, en inglés, antes de la respuesta en español).
PALABRAS_RAZONAMIENTO = frozenset(
    "the we need answer must should according probably provide rules format user data "
    "here not so but let's maybe".split()
)


def parece_razonamiento(texto):
    palabras = [p.strip(".,:;!?\"'()«»").lower() for p in (texto or "").split()]
    return sum(1 for p in palabras if p in PALABRAS_RAZONAMIENTO) >= 6


def enviar(mensajes, herramientas, timeout, config=None):
    """Manda la conversación y devuelve `choices[0].message` del servicio. Si el modelo deja ver
    su razonamiento interno en el texto, se pide la respuesta otra vez, una sola vez."""
    mensaje = _enviar(mensajes, herramientas, timeout, config)
    if not mensaje.get("tool_calls") and parece_razonamiento(mensaje.get("content")):
        logger.warning("Asistente: el modelo mostró su razonamiento; se pide de nuevo.")
        aviso = {
            "role": "system",
            "content": "Respondé solo con la respuesta final, en español, sin explicar cómo la "
            "pensaste.",
        }
        mensaje = _enviar([*mensajes, aviso], herramientas, timeout, config)
    return mensaje


def _enviar(mensajes, herramientas, timeout, config=None):
    config = config or configuracion.actual()
    cuerpo = {"model": config.modelo, "temperature": 0, "messages": mensajes}
    if "gpt-oss" in config.modelo:
        # Groq: el razonamiento de gpt-oss queda fuera de la respuesta y se piensa menos.
        cuerpo.update(include_reasoning=False, reasoning_effort="low")
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
        raise falla(error_http(error.code, error.headers)) from error
    except OSError as error:
        # URLError, TimeoutError y socket.timeout son OSError.
        raise falla(ServicioNoDisponible("sin respuesta")) from error
    try:
        return json.loads(cuerpo_respuesta.decode("utf-8"))["choices"][0]["message"]
    except (ValueError, KeyError, IndexError, TypeError, AttributeError) as error:
        raise falla(ServicioNoDisponible("respuesta inválida")) from error


def error_http(codigo, cabeceras=None):
    """Traduce el código HTTP del servicio (contracts/servicio-ia.md)."""
    if codigo == 429:
        return CuotaAgotada("cuota agotada", segundos_retry_after(cabeceras))
    if codigo in (401, 403):
        # Para el usuario es «no disponible»; el log le dice a quien administra que es la clave.
        return ServicioNoDisponible("clave inválida o sin acceso (401/403)")
    return ServicioNoDisponible(f"error HTTP {codigo}")


def segundos_retry_after(cabeceras):
    """Retry-After en segundos («2», «0.5»); la forma de fecha HTTP no se usa (None)."""
    valor = (cabeceras or {}).get("Retry-After")
    try:
        segundos = float(str(valor).strip())
    except (TypeError, ValueError):
        return None
    return segundos if math.isfinite(segundos) and segundos >= 0 else None


def falla(error):
    """Registra el motivo (nunca la clave, la pregunta ni los datos enviados) y lo devuelve."""
    logger.warning("Asistente: %s.", error.motivo)
    return error
