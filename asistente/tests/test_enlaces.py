"""Reconocimiento de menciones en el texto del modelo (research R8; B de T053)."""

import pytest

from asistente.enlaces import elegir_enlaces
from asistente.herramientas import referencia_estudio


class EstudioFalso:
    pk = 42


ESTUDIO = referencia_estudio(EstudioFalso())


@pytest.mark.parametrize(
    "texto",
    [
        "El Estudio 42 está Finalizado.",
        "En el estudio n.º 42 (PI 200039) no hay pruebas fuera de norma.",
        "Último estudio (n.º 48 no) y el (n.º 42, tipo Físico-químico básico).",
        "Estudio N° 42",
        "estudio nº 42",
        "Estudio #43 y Estudio #42",
        "el estudio número 42",
        "el estudio Nro. 42",
        "tiene un estudio asociado (n.º 42, tipo “Físico‑químico básico”)",
        "ESTUDIO N.º 42",
        "Estudio más reciente\n‑ Número 42 – Bacteriológico básico",
        "- Nro. 42 – Finalizado",
    ],
)
def test_menciones_del_estudio(texto):
    assert elegir_enlaces(texto, [ESTUDIO], []) == [ESTUDIO.enlace()]


@pytest.mark.parametrize(
    "texto",
    [
        "El Estudio 420 está Finalizado.",
        "La muestra PI 200042 está Ingresada.",
        "N° PI 42",
        "Tiene 42 pruebas.",
        "el estudio n.º 4200",
        "Número de pruebas: 42",
        "número 4200",
    ],
)
def test_no_son_menciones_del_estudio(texto):
    assert elegir_enlaces(texto, [ESTUDIO], []) == []


def test_opciones_van_primero_y_con_pregunta():
    from asistente.enlaces import Referencia

    opcion = Referencia("estudio", 7, "Estudio 7", pregunta="¿Qué no cumple en el estudio 7?")
    enlaces = elegir_enlaces(
        "Hay varios; ¿cuál? El Estudio 42 también.", [ESTUDIO], [], opciones=[opcion]
    )
    assert enlaces == [
        {
            "etiqueta": "Estudio 7",
            "url": "/estudios/7/",
            "pregunta": "¿Qué no cumple en el estudio 7?",
        },
        ESTUDIO.enlace(),
    ]
    assert "pregunta" not in ESTUDIO.enlace()
