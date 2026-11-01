import re
from decimal import Decimal

from django.core.exceptions import ValidationError

MAX_DECIMALES = 6
MAX_ENTEROS = 12
FORMATO = re.compile(r"[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)")

# Pruebas de presencia/ausencia (unidad «A/P» en el catálogo, ej. E. coli): la medición se guarda
# como 0 (Ausente) o 1 (Presente) y se muestra siempre como texto.
UNIDAD_PRESENCIA = "A/P"
PRESENCIA = {"ausente": Decimal(0), "presente": Decimal(1)}
OPCIONES_PRESENCIA = [("", "Elegí"), ("Ausente", "Ausente"), ("Presente", "Presente")]


def es_presencia(unidad):
    return (unidad or "").strip().upper() == UNIDAD_PRESENCIA


def texto_presencia(valor):
    """Texto de un valor A/P: 0 → "Ausente", 1 → "Presente"; otro valor se devuelve tal cual."""
    for texto, numero in PRESENCIA.items():
        if valor is not None and valor == numero:
            return texto.capitalize()
    return valor


def leer_valor(texto, *, presencia=False):
    """Valor de una medición escrito con coma o punto decimal, o `None` si está vacío.

    Devuelve el `Decimal` con los decimales escritos ("7,20" → Decimal("7.20")). Con
    `presencia=True` (pruebas A/P) solo acepta "Ausente" (0) o "Presente" (1).
    """
    texto = (texto or "").strip()
    if not texto:
        return None
    if presencia:
        if texto.casefold() not in PRESENCIA:
            raise ValidationError("Elegí Ausente o Presente.")
        return PRESENCIA[texto.casefold()]
    if not FORMATO.fullmatch(texto):
        raise ValidationError("Ingresá un número válido (usá coma o punto para los decimales).")
    valor = Decimal(texto.replace(",", "."))
    if -valor.as_tuple().exponent > MAX_DECIMALES:
        raise ValidationError("Ingresá como máximo 6 decimales.")
    if max(valor.adjusted() + 1, 0) > MAX_ENTEROS:
        raise ValidationError("El valor es demasiado grande (máximo 12 cifras enteras).")
    return valor
