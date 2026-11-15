"""Herramientas de solo lectura que el asistente ofrece al modelo (contracts/herramientas.md).

Se ejecutan con el usuario que pregunta, dentro de una transacción `READ ONLY` que además siempre
se deshace (research R6): una escritura falla y nada queda en la base. Las salidas solo llevan los
campos de la lista blanca (data-model.md); las referencias para los enlaces quedan en AquaLab y no
se mandan al modelo. Cada historia registra sus herramientas con `@registrar`.
"""

import json
import logging
from dataclasses import dataclass, field

from django.db import connection, transaction

logger = logging.getLogger("asistente")

PEDIDO_INVALIDO = {"encontrado": False, "mensaje": "Pedido inválido."}
NO_SE_PUDO = {"encontrado": False, "mensaje": "No se pudo consultar."}

TIPOS_JSON = {
    "string": (str,),
    "integer": (int,),
    "boolean": (bool,),
}


@dataclass(frozen=True)
class Herramienta:
    definicion: dict
    funcion: object

    @property
    def nombre(self):
        return self.definicion["function"]["name"]


@dataclass
class Ejecucion:
    salida: dict
    referencias: list = field(default_factory=list)
    # Herramienta conocida con argumentos válidos (research R3: si ninguna lo fue, mensaje fijo).
    valida: bool = True


REGISTRO = {}


def registrar(definicion):
    def decorador(funcion):
        herramienta = Herramienta(definicion, funcion)
        REGISTRO[herramienta.nombre] = herramienta
        return funcion

    return decorador


def definiciones():
    """La lista `tools` que se manda al servicio."""
    return [h.definicion for h in REGISTRO.values()]


def argumentos_validos(definicion, argumentos):
    esquema = definicion["function"].get("parameters", {})
    propiedades = esquema.get("properties", {})
    if not isinstance(argumentos, dict) or set(argumentos) - set(propiedades):
        return False
    if any(nombre not in argumentos for nombre in esquema.get("required", [])):
        return False
    for nombre, valor in argumentos.items():
        tipos = TIPOS_JSON.get(propiedades[nombre].get("type"), (object,))
        # En JSON, true no es un entero.
        if not isinstance(valor, tipos) or (bool not in tipos and isinstance(valor, bool)):
            return False
    return True


class _Deshacer(Exception):
    """Fuerza el rollback del bloque de solo lectura (también revierte el READ ONLY)."""


def ejecutar(usuario, nombre, argumentos_json):
    herramienta = REGISTRO.get(nombre)
    if herramienta is None:
        return Ejecucion(PEDIDO_INVALIDO, valida=False)
    try:
        argumentos = json.loads(argumentos_json or "{}")
    except (TypeError, ValueError):
        return Ejecucion(PEDIDO_INVALIDO, valida=False)
    if not argumentos_validos(herramienta.definicion, argumentos):
        return Ejecucion(PEDIDO_INVALIDO, valida=False)
    resultado = None
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
            resultado = herramienta.funcion(usuario, **argumentos)
            raise _Deshacer
    except _Deshacer:
        pass
    except Exception:
        logger.error("Asistente: falló la herramienta %s.", nombre, exc_info=True)
        return Ejecucion(NO_SE_PUDO)
    salida, referencias = resultado
    return Ejecucion(salida, list(referencias))


def puede_ver(usuario, tipo, objeto=None):
    """Única regla de permisos del asistente (research R5): lo mismo que las pantallas. Hoy
    muestras, estudios e informes los ve cualquier empleado con sesión; la ficha y el historial de
    un cliente inactivo se rechazan."""
    if usuario is None or not usuario.is_authenticated or not usuario.is_active:
        return False
    if tipo in ("cliente", "historial"):
        return bool(objeto is None or objeto.activo)
    return True


def datos_cliente(cliente):
    """Lista blanca de un cliente: nunca correo, teléfono, domicilio ni documento (FR-014)."""
    return {"nombre": cliente.nombre_completo, "activo": cliente.activo}
