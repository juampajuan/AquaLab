"""Vista `asistente:preguntar` (contracts/preguntar.md)."""

import json

import pytest
from django.test import Client
from django.urls import reverse

from asistente import views

from .conftest import texto

pytestmark = pytest.mark.django_db

URL = "/asistente/preguntar/"


def preguntar(cliente, datos, **kwargs):
    cuerpo = datos if isinstance(datos, (str, bytes)) else json.dumps(datos)
    return cliente.post(URL, cuerpo, content_type="application/json", **kwargs)


def test_url():
    assert reverse("asistente:preguntar") == URL


def test_get_no_permitido(cliente_http, servicio_simulado):
    assert cliente_http.get(URL).status_code == 405


def test_sin_sesion_redirige_al_login(client, servicio_simulado):
    respuesta = preguntar(client, {"pregunta": "hola"})
    assert respuesta.status_code == 302
    assert reverse("usuarios:login") in respuesta["Location"]
    assert servicio_simulado.llamadas == []


def test_sin_csrf(empleado, servicio_simulado):
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(empleado)
    assert preguntar(cliente, {"pregunta": "hola"}).status_code == 403
    assert servicio_simulado.llamadas == []


@pytest.mark.parametrize(
    "datos",
    [
        {"pregunta": ""},
        {"pregunta": "   "},
        {"pregunta": "x" * 501},
        {"pregunta": 3},
        {},
        "{no es json",
        "[1, 2]",
        {"pregunta": "hola", "historial": [{"rol": "usuario", "texto": "a"}] * 7},
        {"pregunta": "hola", "historial": [{"rol": "sistema", "texto": "a"}]},
        {"pregunta": "hola", "historial": [{"rol": "usuario", "texto": "a" * 4001}]},
        {"pregunta": "hola", "historial": [{"rol": "usuario"}]},
        {"pregunta": "hola", "historial": "texto"},
    ],
)
def test_pregunta_invalida(cliente_http, servicio_simulado, datos):
    respuesta = preguntar(cliente_http, datos)
    assert respuesta.status_code == 400
    assert respuesta.json() == {
        "error": "pregunta_invalida",
        "mensaje": "Escribí una pregunta de hasta 500 caracteres.",
    }
    assert servicio_simulado.llamadas == []


def test_respuesta_normal(cliente_http, servicio_simulado, monkeypatch):
    from asistente import conversacion

    llamadas = []

    def responder(usuario, pregunta, historial, config=None):
        llamadas.append((usuario, pregunta, historial))
        return conversacion.Respuesta("Texto", [{"etiqueta": "PI 1", "url": "/muestras/1/"}])

    monkeypatch.setattr(conversacion, "responder", responder)
    historial = [{"rol": "usuario", "texto": "a"}, {"rol": "asistente", "texto": "b"}]
    respuesta = preguntar(
        cliente_http, {"pregunta": "  ¿Cómo está el PI 200417?  ", "historial": historial}
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "texto": "Texto",
        "enlaces": [{"etiqueta": "PI 1", "url": "/muestras/1/"}],
    }
    [(usuario, pregunta, recibido)] = llamadas
    assert usuario.email == "test-estudio@ejemplo.com"
    assert pregunta == "¿Cómo está el PI 200417?"
    assert recibido == historial


def test_pregunta_de_500_caracteres(cliente_http, servicio_simulado):
    servicio_simulado.guion(texto("Hola"))
    assert preguntar(cliente_http, {"pregunta": "x" * 500}).status_code == 200


def test_tecnico_puede_preguntar(cliente_http, empleado, servicio_simulado):
    """Cualquier empleado con sesión, sin grupos ni permisos (FR-001, Q1 = A)."""
    assert not empleado.groups.exists()
    servicio_simulado.guion(texto("Hola"))
    respuesta = preguntar(cliente_http, {"pregunta": "hola"})
    assert respuesta.status_code == 200
    assert respuesta.json()["texto"]


def test_no_escribe_en_la_sesion(cliente_http, servicio_simulado):
    servicio_simulado.guion(texto("Hola"))
    antes = dict(cliente_http.session.items())
    preguntar(cliente_http, {"pregunta": "hola"})
    assert dict(cliente_http.session.items()) == antes


def test_servicio_no_disponible(cliente_http, servicio_simulado):
    from asistente.cliente_ia import ServicioNoDisponible

    servicio_simulado.guion(ServicioNoDisponible("sin respuesta"))
    respuesta = preguntar(cliente_http, {"pregunta": "hola"})
    assert respuesta.status_code == 503
    assert respuesta.json() == {"error": "no_disponible", "mensaje": views.MENSAJE_NO_DISPONIBLE}


def test_error_inesperado_no_sale_de_la_vista(cliente_http, servicio_simulado):
    servicio_simulado.guion(RuntimeError("bug"))
    respuesta = preguntar(cliente_http, {"pregunta": "hola"})
    assert respuesta.status_code == 503
    assert respuesta.json()["error"] == "no_disponible"
