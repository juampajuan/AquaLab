"""Pedidos de registro en la conversación (US 10.3, research R1, R2, R10)."""

import pytest

from asistente import conversacion

from .conftest import herramienta, texto

pytestmark = pytest.mark.django_db


# --- Corte por verbos (T004) ---


@pytest.mark.parametrize(
    "pregunta",
    [
        "Registrá una muestra de Lácteos del Sur, pozo 2, para un físico-químico básico",
        "Creá un estudio para el PI 200417",
        "cargá una muestra de la escuela",
        "Por favor, registrá un estudio bacteriológico para el PI 200417",
        "Registrá otra muestra de Lácteos del Sur",
        "Creá un nuevo estudio para el PI 200417",
        "¿Registrá la muestra de Lácteos?",
    ],
)
def test_pedidos_de_registro_llegan_al_servicio(servicio_simulado, pregunta):
    servicio_simulado.guion(herramienta("preparar_muestra", {}), texto("¿De qué cliente?"))
    conversacion.responder(None, pregunta, [], reloj=servicio_simulado.reloj)
    assert len(servicio_simulado.llamadas) == 2


@pytest.mark.parametrize(
    "pregunta",
    [
        "Validá el estudio 42",
        "Borrá la muestra 200045",
        "Cargá el pH",
        "Cargá las mediciones del estudio 42",
        "Agregá una prueba al estudio 42",
        "Creá un informe del estudio 42",
        "Registrá la validación del estudio 42",
    ],
)
def test_otros_cambios_siguen_cortados(servicio_simulado, pregunta):
    respuesta = conversacion.responder(None, pregunta, [], reloj=servicio_simulado.reloj)
    assert respuesta.texto == conversacion.MENSAJE_SOLO_CONSULTA
    assert respuesta.enlaces == []
    assert servicio_simulado.llamadas == []


@pytest.mark.parametrize(
    "pregunta", ["Registrá el cliente Juan Pérez", "Por favor, creá un cliente nuevo"]
)
def test_alta_de_cliente_mensaje_fijo(servicio_simulado, pregunta):
    respuesta = conversacion.responder(None, pregunta, [], reloj=servicio_simulado.reloj)
    assert respuesta.texto == conversacion.MENSAJE_ALTA_CLIENTE
    assert respuesta.enlaces == [{"etiqueta": "Registrar cliente", "url": "/clientes/registrar/"}]
    assert servicio_simulado.llamadas == []


def test_mensaje_de_sistema_explica_el_registro():
    sistema = conversacion.MENSAJE_SISTEMA
    assert "preparar_muestra" in sistema
    assert "preparar_estudio" in sistema
    assert "las dos fechas juntas" in sistema
    assert "confirma en el formulario" in sistema
