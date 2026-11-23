"""El asistente solo consulta (FR-011, SC-005, research R6)."""

import json

import pytest

from asistente import conversacion, herramientas
from clientes.models import Cliente
from estudios.models import Estudio, Medicion, PruebaEstudio, Resultado, Validacion
from informes.models import Informe
from muestras.models import Muestra

from .conftest import herramienta, texto

pytestmark = pytest.mark.django_db


def foto():
    """Conteos y valores que no deben cambiar."""
    return {
        "conteos": [
            m.objects.count()
            for m in (
                Muestra,
                Estudio,
                PruebaEstudio,
                Medicion,
                Resultado,
                Validacion,
                Informe,
                Cliente,
            )
        ],
        "muestras": list(Muestra.objects.order_by("pk").values_list("estado")),
        "estudios": list(Estudio.objects.order_by("pk").values_list("estado")),
        "pruebas": list(PruebaEstudio.objects.order_by("pk").values_list("estado")),
        "mediciones": list(Medicion.objects.order_by("pk").values_list("valor")),
        "resultados": list(Resultado.objects.order_by("pk").values_list("valor")),
        "validaciones": list(Validacion.objects.order_by("pk").values_list("anulada")),
        "clientes": list(Cliente.objects.order_by("pk").values_list("activo", "nombre")),
    }


def test_herramientas_en_solo_lectura(monkeypatch, empleado, estudio_completo):
    """Una herramienta que intenta escribir falla («No se pudo consultar.») y nada cambia."""
    definicion = {
        "type": "function",
        "function": {"name": "escribir", "parameters": {"type": "object", "properties": {}}},
    }

    def escribir(usuario):
        Muestra.objects.update(nombre="CAMBIADA")
        return {"encontrado": True}, []

    monkeypatch.setitem(
        herramientas.REGISTRO, "escribir", herramientas.Herramienta(definicion, escribir)
    )
    antes = foto()
    ejecucion = herramientas.ejecutar(empleado, "escribir", "{}")
    assert ejecucion.salida == {"encontrado": False, "mensaje": "No se pudo consultar."}
    assert foto() == antes
    assert not Muestra.objects.filter(nombre="CAMBIADA").exists()
    # La transacción del test sigue admitiendo escrituras: el READ ONLY se deshizo.
    Muestra.objects.update(nombre="Después")


def test_base_igual(empleado, estudio_completo, servicio_simulado):
    servicio_simulado.guion(
        herramienta("buscar_muestra", {"numero_pi": 200001}),
        herramienta("detalle_estudio", {"numero": estudio_completo.pk}),
        texto("La muestra PI 200001 …"),
    )
    antes = foto()
    conversacion.responder(empleado, "¿Cómo está el PI 200001?", [], reloj=servicio_simulado.reloj)
    assert foto() == antes


def test_pedido_de_cambio(cliente_http, estudio_completo, servicio_simulado):
    """«validá el PI 200001» con el modelo respondiendo sin herramientas → mensaje fijo."""
    servicio_simulado.guion(texto("Listo, validé el PI 200001."))
    antes = foto()
    respuesta = cliente_http.post(
        "/asistente/preguntar/",
        json.dumps({"pregunta": "validá el PI 200001"}),
        content_type="application/json",
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "texto": conversacion.MENSAJE_SOLO_CONSULTA,
        "enlaces": conversacion.solo_consulta().enlaces,
    }
    assert foto() == antes
