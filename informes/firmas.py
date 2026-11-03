"""Lectura de la firma profesional dibujada en «Mi firma» (US 7.3).

`leer_firma` es la única lectura de lo que envía el formulario (FR-012): un data URL PNG que se
valida en el servidor solo con la biblioteca estándar (prefijo, base64, tamaño, firma PNG y
dimensiones del bloque IHDR), sin decodificar los píxeles. La firma se guarda en la base porque el
disco de Render no persiste.
"""

import base64
import binascii
import struct

from django.core.exceptions import ValidationError

PREFIJO = "data:image/png;base64,"
FIRMA_PNG = b"\x89PNG\r\n\x1a\n"
TAMANO_MAXIMO = 64 * 1024
ANCHO_MAXIMO = 1200
ALTO_MAXIMO = 400

MENSAJE_INVALIDA = "La firma no es una imagen válida."
MENSAJE_GRANDE = "La firma es demasiado grande."


def leer_firma(texto):
    """Devuelve los bytes del PNG del data URL o lanza ValidationError."""
    if not texto.startswith(PREFIJO):
        raise ValidationError(MENSAJE_INVALIDA, code="invalida")
    codificado = texto[len(PREFIJO) :]
    # Cota previa para no decodificar envíos enormes: base64 ocupa 4/3 de los bytes.
    if len(codificado) > (TAMANO_MAXIMO + 2) // 3 * 4 + 4:
        raise ValidationError(MENSAJE_GRANDE, code="grande")
    try:
        datos = base64.b64decode(codificado, validate=True)
    except (binascii.Error, ValueError):
        raise ValidationError(MENSAJE_INVALIDA, code="invalida") from None
    if len(datos) > TAMANO_MAXIMO:
        raise ValidationError(MENSAJE_GRANDE, code="grande")
    # Firma PNG y el primer bloque, que siempre es IHDR: largo (4), tipo (4), ancho y alto (4 + 4).
    if len(datos) < 24 or not datos.startswith(FIRMA_PNG) or datos[12:16] != b"IHDR":
        raise ValidationError(MENSAJE_INVALIDA, code="invalida")
    ancho, alto = struct.unpack(">II", datos[16:24])
    if not (1 <= ancho <= ANCHO_MAXIMO and 1 <= alto <= ALTO_MAXIMO):
        raise ValidationError(MENSAJE_INVALIDA, code="invalida")
    return datos
