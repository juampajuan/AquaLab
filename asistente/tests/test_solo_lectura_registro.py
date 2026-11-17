"""Abandonar un pedido no deja nada creado (US 10.3, US4, SC-002)."""

import json

import pytest
from django.db import transaction
from django.urls import reverse

from estudios.models import Estudio, TipoEstudio
from muestras.models import Muestra, Origen
from muestras.servicios import siguiente_numero_pi

from .conftest import herramienta, texto

pytestmark = pytest.mark.django_db

URL = reverse("asistente:preguntar")


def foto(cliente_http):
    with transaction.atomic():
        proximo = siguiente_numero_pi()
    return {
        "muestras": Muestra.objects.count(),
        "estudios": Estudio.objects.count(),
        "origenes": sorted(Origen.objects.values_list("nombre", flat=True)),
        "proximo_pi": proximo,
        "sesion": sorted(cliente_http.session.keys()),
    }


def preguntar(cliente_http, pregunta, historial):
    respuesta = cliente_http.post(
        URL,
        json.dumps({"pregunta": pregunta, "historial": historial}),
        content_type="application/json",
    )
    assert respuesta.status_code == 200
    datos = respuesta.json()
    historial += [
        {"rol": "usuario", "texto": pregunta},
        {"rol": "asistente", "texto": datos["texto"]},
    ]
    return datos


def test_pedidos_completos_y_abandonados_no_crean_nada(cliente_http, muestra, servicio_simulado):
    from clientes.models import Cliente

    cliente = Cliente.objects.create(
        razon_social="Lácteos del Sur S.A.", tipo_documento="CUIT", numero_documento="30712345675"
    )
    Origen.objects.create(cliente=cliente, nombre="Pozo 2")
    TipoEstudio.objects.create(nombre="Físico-químico básico")
    antes = foto(cliente_http)

    historial = []
    dicho = {"cliente": "Lácteos del Sur", "origen": "pozo 9", "tipo_estudio": "físico"}
    servicio_simulado.guion(herramienta("preparar_muestra", dicho), texto("¿Cuál origen?"))
    preguntar(cliente_http, "Registrá una muestra de Lácteos del Sur, pozo 9, físico", historial)
    servicio_simulado.guion(
        herramienta("preparar_muestra", {**dicho, "origen_nuevo": True}), texto("¿Fechas?")
    )
    preguntar(cliente_http, "Registrar «pozo 9» como origen nuevo", historial)
    servicio_simulado.guion(
        herramienta(
            "preparar_muestra",
            {**dicho, "origen_nuevo": True, "fecha_muestreo": "hoy", "fecha_ingreso": "hoy"},
        ),
        texto("Listo."),
    )
    final = preguntar(cliente_http, "hoy las dos", historial)
    enlace = final["enlaces"][0]
    assert enlace["etiqueta"] == "Revisar y registrar la muestra"

    servicio_simulado.guion(
        herramienta("preparar_estudio", {"numero_pi": muestra.numero_pi, "tipo_estudio": "físico"}),
        texto("Listo."),
    )
    estudio = preguntar(
        cliente_http, f"Creá un estudio físico-químico para el PI {muestra.numero_pi}", []
    )
    assert foto(cliente_http) == antes

    # Abrir los formularios precargados y no enviarlos tampoco crea nada (la sesión de registro
    # de muestra se descarta al abrir uno nuevo, como siempre).
    assert cliente_http.get(enlace["url"]).status_code == 200
    assert cliente_http.get(estudio["enlaces"][0]["url"]).status_code == 200
    despues = foto(cliente_http)
    assert {k: v for k, v in despues.items() if k != "sesion"} == {
        k: v for k, v in antes.items() if k != "sesion"
    }
    assert "muestra_pendiente" not in cliente_http.session
