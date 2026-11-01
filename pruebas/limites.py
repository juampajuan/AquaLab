"""Interpretación de los límites del catálogo para evaluar un resultado (US 6.4).

Los límites se guardan como texto tal como vienen del laboratorio (SCRUM-64): números, «Ausente» o
«Ausencia», y textos que no se pueden comparar («SOE», «NE», «Ph-0,2»). Esta es la única forma de
leerlos; no accede a la base salvo por los límites por vertido ya cargados en la prueba.
"""

import re
from dataclasses import dataclass
from decimal import Decimal

from django.db import models

NUMERO = re.compile(r"[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)")
AUSENTE = "ausente"
NO_COMPARABLE = "no_comparable"
TEXTOS_AUSENTE = {"ausente", "ausencia"}


class Evaluacion(models.TextChoices):
    CUMPLE = "cumple", "Cumple"
    FUERA_DE_NORMA = "fuera_de_norma", "Fuera de norma"
    SIN_LIMITE = "sin_limite", "Sin límite comparable"


@dataclass(frozen=True)
class LimitesAplicables:
    """Límites que corresponden a un resultado, con los textos tal como están en el catálogo."""

    minimo: str
    maximo: str
    norma: str
    origen: str  # "general" o el tipo de vertido cuyos límites se usaron


def leer_limite(texto):
    """`Decimal`, `AUSENTE`, `None` (sin límite) o `NO_COMPARABLE` para el texto del catálogo."""
    texto = (texto or "").strip()
    if not texto:
        return None
    if texto.casefold() in TEXTOS_AUSENTE:
        return AUSENTE
    if NUMERO.fullmatch(texto):
        return Decimal(texto.replace(",", "."))
    return NO_COMPARABLE


def limites_aplicables(prueba, tipo_vertido):
    """Los límites del tipo de vertido de la muestra si la prueba los tiene; si no, los generales.

    Los del vertido reemplazan a los generales completos. Usa `prueba.limites_vertido.all()`, así
    aprovecha un `prefetch_related` del llamador.
    """
    for limite in prueba.limites_vertido.all():
        if limite.tipo_vertido == tipo_vertido:
            return LimitesAplicables(
                limite.limite_min, limite.limite_max, limite.norma, limite.tipo_vertido
            )
    return LimitesAplicables(prueba.limite_min, prueba.limite_max, prueba.norma, "general")


def evaluar(valor, limites):
    """Cumple, fuera de norma o sin límite comparable (FR-007 de la spec 019).

    Compara el valor completo del resultado, no el redondeado que se muestra.
    """
    minimo, maximo = leer_limite(limites.minimo), leer_limite(limites.maximo)
    if NO_COMPARABLE in (minimo, maximo) or (minimo is None and maximo is None):
        return Evaluacion.SIN_LIMITE
    if AUSENTE in (minimo, maximo):
        return Evaluacion.CUMPLE if valor == 0 else Evaluacion.FUERA_DE_NORMA
    if minimo is not None and valor < minimo:
        return Evaluacion.FUERA_DE_NORMA
    if maximo is not None and valor > maximo:
        return Evaluacion.FUERA_DE_NORMA
    return Evaluacion.CUMPLE
