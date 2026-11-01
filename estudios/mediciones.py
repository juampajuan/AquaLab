import re
from decimal import Decimal

from django.core.exceptions import ValidationError

MAX_DECIMALES = 6
MAX_ENTEROS = 12
FORMATO = re.compile(r"[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)")


def leer_valor(texto):
    """Valor de una medición escrito con coma o punto decimal, o `None` si está vacío.

    Devuelve el `Decimal` con los decimales escritos ("7,20" → Decimal("7.20")).
    """
    texto = (texto or "").strip()
    if not texto:
        return None
    if not FORMATO.fullmatch(texto):
        raise ValidationError("Ingresá un número válido (usá coma o punto para los decimales).")
    valor = Decimal(texto.replace(",", "."))
    if -valor.as_tuple().exponent > MAX_DECIMALES:
        raise ValidationError("Ingresá como máximo 6 decimales.")
    if max(valor.adjusted() + 1, 0) > MAX_ENTEROS:
        raise ValidationError("El valor es demasiado grande (máximo 12 cifras enteras).")
    return valor
