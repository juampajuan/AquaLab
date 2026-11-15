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


# --- US4: servicio no disponible ---


def test_cuota_agotada(cliente_http, servicio_simulado):
    """US4 Esc. 2."""
    from asistente.cliente_ia import CuotaAgotada

    servicio_simulado.guion(CuotaAgotada("cuota agotada"))
    respuesta = preguntar(cliente_http, {"pregunta": "hola"})
    assert respuesta.status_code == 429
    assert respuesta.json() == {
        "error": "cuota",
        "mensaje": (
            "Se alcanzó el límite de consultas del asistente. Probá más tarde; el resto de "
            "AquaLab funciona normalmente."
        ),
    }


def test_no_disponible_mensaje_literal(cliente_http, servicio_simulado):
    """US4 Esc. 1."""
    from asistente.cliente_ia import ServicioNoDisponible

    servicio_simulado.guion(ServicioNoDisponible("sin respuesta"))
    assert preguntar(cliente_http, {"pregunta": "hola"}).json() == {
        "error": "no_disponible",
        "mensaje": (
            "El asistente no está disponible en este momento. Probá de nuevo más tarde o usá "
            "las pantallas de AquaLab."
        ),
    }


def test_sin_clave_no_configurado(cliente_http, settings, monkeypatch):
    """US4 Esc. 3: sin clave no se llama al servicio."""
    from asistente import cliente_ia

    settings.ASISTENTE = {"clave": ""}
    llamadas = []
    monkeypatch.setattr(cliente_ia, "enviar", lambda *a, **k: llamadas.append(a))
    respuesta = preguntar(cliente_http, {"pregunta": "hola"})
    assert respuesta.status_code == 503
    assert respuesta.json() == {
        "error": "no_configurado",
        "mensaje": "El asistente no está configurado.",
    }
    assert llamadas == []


def test_segunda_llamada_lenta_503(cliente_http, servicio_simulado, monkeypatch):
    """El tiempo agotado por demora del servicio da 503; el tope de vueltas, 200."""
    from asistente import herramientas

    from .conftest import Lenta, herramienta

    definicion = {
        "type": "function",
        "function": {"name": "eco", "parameters": {"type": "object", "properties": {}}},
    }
    monkeypatch.setitem(
        herramientas.REGISTRO,
        "eco",
        herramientas.Herramienta(definicion, lambda usuario: ({"encontrado": True}, [])),
    )
    servicio_simulado.guion(herramienta("eco"), Lenta(30, texto("tarde")))
    respuesta = preguntar(cliente_http, {"pregunta": "hola"})
    assert respuesta.status_code == 503
    assert respuesta.json()["error"] == "no_disponible"
    servicio_simulado.guion(*[herramienta("eco") for _ in range(7)])
    respuesta = preguntar(cliente_http, {"pregunta": "hola"})
    assert respuesta.status_code == 200
    assert respuesta.json()["texto"] == (
        "No pude completar la consulta; probá con una pregunta más concreta."
    )


def test_despues_de_una_falla_se_puede_preguntar(cliente_http, servicio_simulado):
    """US4 Esc. 1: otra pregunta funciona después de una falla."""
    from asistente.cliente_ia import CuotaAgotada, ServicioNoDisponible

    servicio_simulado.guion(
        ServicioNoDisponible("sin respuesta"), CuotaAgotada("cuota agotada"), texto("Hola")
    )
    assert preguntar(cliente_http, {"pregunta": "a"}).status_code == 503
    assert preguntar(cliente_http, {"pregunta": "b"}).status_code == 429
    assert preguntar(cliente_http, {"pregunta": "c"}).status_code == 200


@pytest.mark.parametrize("ruta", ["inicio", "estudios:buscar", "clientes:buscar"])
def test_pantallas_con_el_servicio_caido(cliente_http, servicio_simulado, ruta):
    """US4 Esc. 5, FR-017: el resto de AquaLab no depende del servicio."""
    from asistente.cliente_ia import ServicioNoDisponible

    servicio_simulado.guion(ServicioNoDisponible("sin respuesta"))
    preguntar(cliente_http, {"pregunta": "hola"})
    assert cliente_http.get(reverse(ruta)).status_code == 200
    assert servicio_simulado.llamadas[1:] == []
