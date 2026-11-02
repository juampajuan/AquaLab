import base64

import pytest
from django.core.exceptions import ValidationError

from informes.firmas import TAMANO_MAXIMO, leer_firma

from .utiles import data_url, png

INVALIDA = "La firma no es una imagen válida."
GRANDE = "La firma es demasiado grande."


def test_leer_firma_valida():
    datos = png()
    assert leer_firma(data_url(datos)) == datos


def test_leer_firma_en_los_bordes():
    datos = png(1200, 400)
    assert leer_firma(data_url(datos)) == datos
    assert leer_firma(data_url(png(1, 1))) == png(1, 1)


@pytest.mark.parametrize(
    ("texto", "mensaje"),
    [
        (data_url(png(), tipo="image/jpeg"), INVALIDA),
        ("data:image/png;base64,esto no es base64!", INVALIDA),
        ("iVBORw0KGgo", INVALIDA),
        (data_url(b"GIF89a" + b"\x00" * 40), INVALIDA),
        (data_url(b"\x89PNG\r\n\x1a\n"), INVALIDA),
        (data_url(png(0, 200)), INVALIDA),
        (data_url(png(1201, 200)), INVALIDA),
        (data_url(png(600, 401)), INVALIDA),
        (data_url(png(relleno=b"x" * (TAMANO_MAXIMO + 1))), GRANDE),
    ],
    ids=[
        "jpeg",
        "base64-invalido",
        "sin-prefijo",
        "no-es-png",
        "png-truncado",
        "ancho-cero",
        "ancho-excedido",
        "alto-excedido",
        "demasiado-grande",
    ],
)
def test_leer_firma_rechaza(texto, mensaje):
    with pytest.raises(ValidationError) as exc:
        leer_firma(texto)
    assert exc.value.messages == [mensaje]


def test_tamano_maximo_es_64_kb():
    assert TAMANO_MAXIMO == 64 * 1024


def test_limite_exacto_de_tamano():
    base = png()
    relleno = TAMANO_MAXIMO - len(base) - 12 - len(b"relleno\x00")
    datos = png(relleno=b"x" * relleno)
    assert len(datos) == TAMANO_MAXIMO
    assert leer_firma(data_url(datos)) == datos
    assert base64.b64decode(data_url(datos).split(",", 1)[1]) == datos
