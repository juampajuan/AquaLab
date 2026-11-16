"""Fixtures del asistente (US 10.1). Ningún test llama al servicio de IA (research R1)."""

import json
import urllib.request

import pytest
from django.utils import timezone

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


@pytest.fixture
def estudio_completo(estudio_de, empleado, bioquimico):
    """Estudio de la muestra PI 200001 con una prueba de cada caso (US1 del asistente):
    PH 7,2 cumple y CL- 40 → 400 fuera de norma (validadas); COND sin límite comparable, ECOLI
    Ausente y TURBIDEZ bajo el LD (Cargadas, sin validar); TEMPERATURA Pendiente."""
    from estudios.tests.utiles import cargar, validar

    estudio = estudio_de("PH", "CL-", "COND", "ECOLI", "TURBIDEZ", "TEMPERATURA")
    cargar(
        estudio,
        empleado,
        {"PH": "7.2", "CL-": "40", "COND": "500", "ECOLI": "0", "TURBIDEZ": "0.05"},
    )
    validar(estudio, bioquimico, "PH", "CL-")
    estudio.refresh_from_db()
    return estudio


def ejecutar(usuario, nombre, **argumentos):
    """Ejecuta una herramienta como lo hace la conversación y devuelve la `Ejecucion`."""
    from asistente import herramientas

    return herramientas.ejecutar(usuario, nombre, json.dumps(argumentos))


@pytest.fixture
def escuela(cliente_a, estudio_en_origen):
    """Dos estudios de «Escuela Técnica N° 12» (US2): el más viejo con CL- fuera de norma."""
    import datetime

    from muestras.models import Origen

    origen = Origen.objects.create(cliente=cliente_a, nombre="Escuela Técnica N° 12")
    hoy = timezone.localdate()
    viejo = estudio_en_origen(
        origen, hoy - datetime.timedelta(days=30), 200101, {"PH": "7.2", "CL-": "40"}
    )
    nuevo = estudio_en_origen(origen, hoy, 200102, {"PH": "7.0"})
    return {"origen": origen, "viejo": viejo, "nuevo": nuevo}


@pytest.fixture
def lacteos(empleado, estudio_en_origen):
    """«Lácteos del Sur S.A.» con 12 estudios en dos orígenes (US3), con contacto completo."""
    import datetime

    from clientes.models import Cliente
    from muestras.models import Origen

    cliente = Cliente.objects.create(
        razon_social="Lácteos del Sur S.A.",
        tipo_documento="CUIT",
        numero_documento="30712345675",
        email="contacto@lacteos.test",
        telefono="+54 11 5555-0101",
        domicilio="Ruta 5 km 112",
    )
    planta = Origen.objects.create(cliente=cliente, nombre="Planta")
    pozo = Origen.objects.create(cliente=cliente, nombre="Pozo de la planta")
    hoy = timezone.localdate()
    estudios = [
        estudio_en_origen(
            planta if i % 2 else pozo,
            hoy - datetime.timedelta(days=i),
            200200 + i,
            {"PH": "7.1"},
            validar_todo=i % 3 == 0,
        )
        for i in range(12)
    ]
    return {"cliente": cliente, "estudios": estudios}
