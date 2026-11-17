import json
import threading
from dataclasses import replace

import pytest

from asistente import cliente_ia, configuracion
from informes import conclusion_ia


@pytest.fixture
def hechos():
    return {
        "clase": "con_incumplimientos",
        "pruebas": [
            {
                "codigo": "PH",
                "nombre": "pH",
                "resultado_texto": "9,2",
                "unidad": "pH",
                "limite_texto": "máx. 8.5",
                "norma": "CAA",
                "clase_conclusion": "fuera_de_norma",
            }
        ],
    }


@pytest.fixture
def config():
    return configuracion.Configuracion("ficticia-test", configuracion.URL_GROQ, "modelo-test")


def respuesta(bloques=None, cierre="I1", **extra):
    contenido = {
        "version": "1",
        "bloques": bloques if bloques is not None else [{"hecho": "h1", "redaccion": "F1"}],
        "cierre": cierre,
        **extra,
    }
    return {"role": "assistant", "content": json.dumps(contenido)}


def test_reutiliza_cliente_y_privacidad(monkeypatch, hechos, config):
    llamadas = []

    def enviar(mensajes, herramientas, timeout, config=None):
        llamadas.append((mensajes, herramientas, timeout, config))
        return respuesta()

    monkeypatch.setattr(cliente_ia, "enviar", enviar)
    propuesta = conclusion_ia.proponer(hechos, config=config)
    assert propuesta.origen == "ia"
    assert "9,2" in propuesta.texto and "CAA" in propuesta.texto
    mensajes, herramientas, timeout, usado = llamadas[0]
    enviado = json.dumps(mensajes)
    assert all(dato not in enviado for dato in ("9,2", "CAA", "máx. 8.5", "ficticia-test"))
    assert herramientas == []
    assert timeout <= config.timeout
    assert usado == config


@pytest.mark.parametrize(
    "mala",
    [
        {"content": ""},
        {"content": "texto inventado"},
        respuesta([], "I1"),
        respuesta(cierre="T1"),
        respuesta(extra="hechos inventados"),
        respuesta([{"hecho": "h2", "redaccion": "F1"}]),
        respuesta([{"hecho": "h1", "redaccion": "F1"}] * 2),
        {**respuesta(), "tool_calls": [{"id": "prohibido"}]},
    ],
)
def test_gramatica_invalida_respaldo(monkeypatch, hechos, config, mala):
    monkeypatch.setattr(cliente_ia, "enviar", lambda *args, **kwargs: mala)
    propuesta = conclusion_ia.proponer(hechos, config=config)
    assert propuesta.origen == "plantilla"
    assert propuesta.motivo == "respuesta_invalida"
    assert propuesta.texto == conclusion_ia.plantilla(hechos)


@pytest.mark.parametrize(
    "error,motivo",
    [
        (cliente_ia.CuotaAgotada("cuota"), "cuota"),
        (cliente_ia.ServicioNoDisponible("falla"), "no_disponible"),
        (OSError("red"), "no_disponible"),
    ],
)
def test_fallos_conservan_hechos(monkeypatch, hechos, config, error, motivo):
    def fallar(*args, **kwargs):
        raise error

    monkeypatch.setattr(cliente_ia, "enviar", fallar)
    propuesta = conclusion_ia.proponer(hechos, config=config)
    assert propuesta.motivo == motivo
    assert propuesta.texto == conclusion_ia.plantilla(hechos)


def test_sin_configuracion_no_hay_red(monkeypatch, hechos, config):
    monkeypatch.setattr(cliente_ia, "enviar", lambda *a, **kw: pytest.fail("Red inesperada"))
    propuesta = conclusion_ia.proponer(hechos, config=replace(config, clave=""))
    assert propuesta.motivo == "sin_configuracion"


@pytest.mark.parametrize("clase,cierre", [("todas_cumplen", "T1"), ("parcial", "P1")])
def test_cierres_sin_incumplimientos(monkeypatch, config, clase, cierre):
    monkeypatch.setattr(cliente_ia, "enviar", lambda *a, **kw: respuesta([], cierre))
    propuesta = conclusion_ia.proponer({"clase": clase, "pruebas": []}, config=config)
    assert propuesta.origen == "ia"
    assert ("Todas" in propuesta.texto) == (clase == "todas_cumplen")


def test_tamano_no_trunca_plantilla(monkeypatch, hechos, config):
    monkeypatch.setattr(cliente_ia, "enviar", lambda *a, **kw: {"content": "x" * 65537})
    propuesta = conclusion_ia.proponer(hechos, config=config)
    assert propuesta.motivo == "tamano"
    assert "9,2" in propuesta.texto


def test_plazo_capacidad_y_liberacion(monkeypatch, hechos, config):
    capacidad = threading.BoundedSemaphore(2)
    monkeypatch.setattr(conclusion_ia, "_capacidad", capacidad)
    terminar = threading.Event()
    iniciados = threading.Barrier(3)
    finalizados = threading.Barrier(3)

    def lento(*a, **kw):
        iniciados.wait(timeout=5)
        terminar.wait(timeout=5)
        finalizados.wait(timeout=5)
        return respuesta()

    monkeypatch.setattr(cliente_ia, "enviar", lento)
    config = replace(config, presupuesto=0.1)
    propuestas = []
    hilos = [
        threading.Thread(
            target=lambda: propuestas.append(conclusion_ia.proponer(hechos, config=config))
        )
        for _ in range(2)
    ]
    try:
        for hilo in hilos:
            hilo.start()
        iniciados.wait(timeout=5)
        for hilo in hilos:
            hilo.join(timeout=2)
            assert not hilo.is_alive()
        assert all(p.motivo == "plazo" for p in propuestas)
        assert conclusion_ia.proponer(hechos, config=config).motivo == "capacidad"
    finally:
        terminar.set()
        finalizados.wait(timeout=5)
    assert capacidad.acquire(timeout=2)
    assert capacidad.acquire(timeout=2)
    capacidad.release()
    capacidad.release()
