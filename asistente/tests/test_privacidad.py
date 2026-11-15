"""Al servicio externo no van datos de contacto del cliente ni datos de usuarios (FR-014,
SC-006)."""

import json

import pytest

from .conftest import herramienta, texto

pytestmark = pytest.mark.django_db


def test_nada_de_contacto_ni_usuarios(cliente_http, empleado, lacteos, servicio_simulado):
    cliente = lacteos["cliente"]
    estudio = lacteos["estudios"][0]
    servicio_simulado.guion(
        herramienta("buscar_cliente", {"texto": "lácteos"}),
        herramienta("estudios_de_cliente", {"cliente_id": cliente.pk}),
        herramienta("buscar_muestra", {"numero_pi": 200200}),
        herramienta("detalle_estudio", {"numero": estudio.pk}),
        herramienta("buscar_muestra", {"texto": "planta"}),
        texto(f"Lácteos del Sur S.A. tiene el Estudio {estudio.pk} Finalizado."),
    )
    respuesta = cliente_http.post(
        "/asistente/preguntar/",
        json.dumps({"pregunta": "¿Qué estudios tiene Lácteos del Sur?"}),
        content_type="application/json",
    )
    assert respuesta.status_code == 200
    enviado = json.dumps([ll["mensajes"] for ll in servicio_simulado.llamadas], ensure_ascii=False)
    al_navegador = respuesta.content.decode()
    # Todas las herramientas respondieron con datos (no «Pedido inválido.»).
    respuestas_tool = [
        json.loads(m["content"])
        for m in servicio_simulado.llamadas[-1]["mensajes"]
        if m["role"] == "tool"
    ]
    assert [r["encontrado"] for r in respuestas_tool] == [True] * 5
    prohibidos = (
        cliente.email,
        cliente.telefono,
        cliente.domicilio,
        cliente.numero_documento,
        empleado.email,
        empleado.get_full_name(),
    )
    for prohibido in prohibidos:
        assert prohibido not in enviado, prohibido
        assert prohibido not in al_navegador, prohibido
