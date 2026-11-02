"""Ayudas para los tests de la firma (US 7.3): PNG mínimos armados sin Pillow."""

import base64
import struct
import zlib


def _bloque(tipo, datos):
    crc = zlib.crc32(tipo + datos) & 0xFFFFFFFF
    return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", crc)


def png(ancho=600, alto=200, relleno=b""):
    """PNG válido en escala de grises de ese tamaño; `relleno` agrega un bloque de texto (tEXt)
    para inflar el archivo sin cambiar la imagen."""
    ihdr = struct.pack(">IIBBBBB", ancho, alto, 8, 0, 0, 0, 0)
    filas = b"".join(b"\x00" + b"\xff" * ancho for _ in range(alto))
    bloques = _bloque(b"IHDR", ihdr) + _bloque(b"IDAT", zlib.compress(filas, 9))
    if relleno:
        bloques += _bloque(b"tEXt", b"relleno\x00" + relleno)
    return b"\x89PNG\r\n\x1a\n" + bloques + _bloque(b"IEND", b"")


def data_url(datos, tipo="image/png"):
    return f"data:{tipo};base64," + base64.b64encode(datos).decode()
