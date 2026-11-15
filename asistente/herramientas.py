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
class Salida:
    """Lo que devuelve una herramienta: `datos` va al modelo; lo demás queda en AquaLab."""

    datos: dict
    referencias: list = field(default_factory=list)
    # Textos que AquaLab agrega al final de la respuesta y referencias que van primero (FR-009a).
    avisos: list = field(default_factory=list)
    primeras: list = field(default_factory=list)


@dataclass
class Ejecucion:
    salida: dict
    referencias: list = field(default_factory=list)
    # Herramienta conocida con argumentos válidos (research R3: si ninguna lo fue, mensaje fijo).
    valida: bool = True
    avisos: list = field(default_factory=list)
    primeras: list = field(default_factory=list)


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
    if not isinstance(resultado, Salida):
        resultado = Salida(*resultado)
    return Ejecucion(
        resultado.datos,
        list(resultado.referencias),
        avisos=list(resultado.avisos),
        primeras=list(resultado.primeras),
    )


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


# --- Consultas (cada una replica la consulta de su pantalla, research R4) ---

FORMATO_FECHA = "%d/%m/%Y"
ESTUDIOS_POR_MUESTRA = 5  # una vuelta para la muestra y una por estudio (max_vueltas − 1)
MAX_LISTA = 10
MAX_NUMERO_SQL = 2_147_483_647


def fecha(valor):
    from django.utils import timezone

    if valor is None:
        return ""
    if hasattr(valor, "hour"):
        valor = timezone.localdate(valor)
    return valor.strftime(FORMATO_FECHA)


def referencia_muestra(muestra):
    from .enlaces import Referencia

    numero = str(muestra.numero_pi)
    return Referencia("muestra", muestra.pk, f"PI {numero}", claves=(f"PI {numero}", numero))


def referencia_estudio(estudio):
    from .enlaces import Referencia

    numero = estudio.pk
    return Referencia(
        "estudio",
        numero,
        f"Estudio {numero}",
        claves=(f"Estudio {numero}", f"Estudio N° {numero}", f"Estudio Nº {numero}"),
    )


def referencia_cliente(usuario, cliente):
    """La ficha del cliente, solo si quien pregunta la puede abrir (cliente activo)."""
    from .enlaces import Referencia

    if not puede_ver(usuario, "cliente", cliente):
        return []
    claves = tuple(c for c in (cliente.nombre_completo, cliente.razon_social, cliente.nombre) if c)
    return [Referencia("cliente", cliente.pk, cliente.nombre_completo, claves=claves)]


def referencia_informe(estudio):
    from .enlaces import Referencia

    return Referencia(
        "informe",
        estudio.pk,
        f"Informe del estudio {estudio.pk}",
        claves=(f"Informe del estudio {estudio.pk}",),
    )


def tiene_informe(estudio):
    from django.core.exceptions import ObjectDoesNotExist

    try:
        return estudio.informe is not None
    except ObjectDoesNotExist:
        return False


def no_encontrado(mensaje):
    return Salida({"encontrado": False, "mensaje": mensaje})


@registrar(
    {
        "type": "function",
        "function": {
            "name": "buscar_muestra",
            "description": (
                "Busca una muestra por su N° PI (exacto) o por texto (nombre de la muestra, del "
                "origen o del cliente). Con el N° PI devuelve la muestra y sus estudios más "
                "recientes; para ver las pruebas de un estudio usá detalle_estudio."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "numero_pi": {"type": "integer", "description": "N° PI, por ejemplo 200417."},
                    "texto": {"type": "string", "description": "Muestra, origen o cliente."},
                },
            },
        },
    }
)
def buscar_muestra(usuario, numero_pi=None, texto=None):
    from django.db.models import Count, Q

    from muestras.models import Muestra
    from muestras.views import estudios_de_la_ficha

    if numero_pi is not None:
        mensaje = f"No hay ninguna muestra con el N° PI {numero_pi}."
        if not 0 < numero_pi <= MAX_NUMERO_SQL:
            return no_encontrado(mensaje)
        muestra = (
            Muestra.objects.select_related("cliente", "origen").filter(numero_pi=numero_pi).first()
        )
        if muestra is None or not puede_ver(usuario, "muestra", muestra):
            return no_encontrado(mensaje)
        estudios = list(estudios_de_la_ficha(muestra).select_related("informe"))
        recientes = estudios[:ESTUDIOS_POR_MUESTRA]
        datos = {
            **datos_muestra(muestra),
            "total_estudios": len(estudios),
            "estudios": [
                {
                    "numero": e.pk,
                    "tipo": e.tipo_nombre_snapshot,
                    "estado": e.get_estado_display(),
                    "pruebas_completadas": e.pruebas_completadas,
                    "total_pruebas": e.total_pruebas,
                    "con_informe": tiene_informe(e),
                }
                for e in recientes
            ],
        }
        salida = {"encontrado": True, "datos": datos}
        avisos, primeras = [], []
        if len(estudios) > ESTUDIOS_POR_MUESTRA:
            total = len(estudios)
            salida["mensaje"] = (
                f"La muestra tiene {total} estudios; se detallan los "
                f"{ESTUDIOS_POR_MUESTRA} más recientes."
            )
            avisos.append(
                f"La muestra PI {muestra.numero_pi} tiene {total} estudios; se detallan los "
                f"{ESTUDIOS_POR_MUESTRA} más recientes. El resto está en la ficha de la muestra."
            )
            primeras.append(referencia_muestra(muestra))
        referencias = [
            referencia_muestra(muestra),
            *(referencia_estudio(e) for e in recientes),
            *referencia_cliente(usuario, muestra.cliente),
        ]
        return Salida(salida, referencias, avisos, primeras)
    texto = (texto or "").strip()
    if not texto:
        return no_encontrado("Indicá el N° PI o un texto para buscar la muestra.")
    filtro = (
        Q(nombre__unaccent__icontains=texto)
        | Q(origen__nombre__unaccent__icontains=texto)
        | Q(cliente__nombre__unaccent__icontains=texto)
        | Q(cliente__razon_social__unaccent__icontains=texto)
    )
    qs = (
        Muestra.objects.filter(filtro)
        .select_related("cliente", "origen")
        .annotate(total_estudios=Count("estudios"))
        .order_by("-fecha_ingreso", "-numero_pi")
    )
    total = qs.count()
    if not total:
        return no_encontrado(f"No hay muestras que coincidan con «{texto}».")
    muestras = list(qs[:MAX_LISTA])
    datos = {
        "muestras": [
            {
                "numero_pi": m.numero_pi,
                "nombre": m.nombre,
                "cliente": m.cliente.nombre_completo,
                "origen": m.origen.nombre,
                "fecha_ingreso": fecha(m.fecha_ingreso),
                "total_estudios": m.total_estudios,
            }
            for m in muestras
        ]
    }
    return Salida(
        {"encontrado": True, "total": total, "mostrados": len(muestras), "datos": datos},
        [referencia_muestra(m) for m in muestras],
    )


def datos_muestra(muestra):
    """Lista blanca de una muestra (data-model.md): sin responsable ni quién la registró."""
    return {
        "numero_pi": muestra.numero_pi,
        "nombre": muestra.nombre,
        "cliente": muestra.cliente.nombre_completo,
        "origen": muestra.origen.nombre,
        "estado": muestra.get_estado_display(),
        "fecha_muestreo": fecha(muestra.fecha_muestreo),
        "fecha_ingreso": fecha(muestra.fecha_ingreso),
        "tipo_vertido": muestra.get_tipo_vertido_display(),
        "sitio_extraccion": muestra.sitio_extraccion,
    }


def datos_prueba(asignacion, tipo_vertido):
    """Una prueba del estudio con los textos de pantalla («< LD», «Ausente», coma decimal). Sin
    datos de quién cargó, corrigió o validó (FR-014)."""
    from config.ui import unidad
    from estudios import calculo
    from estudios.mediciones import es_presencia
    from estudios.models import EstadoPruebaEstudio
    from informes.contenido import limites_y_evaluacion, texto_resultado
    from pruebas.limites import Evaluacion

    resultado = ""
    unidad_texto = ""
    if calculo.tiene_resultado(asignacion):
        limites, _ = limites_y_evaluacion(asignacion, tipo_vertido)
        resultado = texto_resultado(asignacion.resultado, limites)
        if not es_presencia(asignacion.resultado.unidad):
            unidad_texto = unidad(asignacion.resultado.unidad)
    evaluacion = getattr(asignacion, "evaluacion", None)
    validada = asignacion.estado == EstadoPruebaEstudio.COMPLETADA
    validacion = getattr(asignacion, "validacion", None)
    return {
        "codigo": asignacion.prueba.codigo,
        "nombre": asignacion.prueba.nombre,
        "estado": asignacion.get_estado_display(),
        "resultado": resultado,
        "unidad": unidad_texto,
        "sin_resultado": asignacion.motivo_sin_resultado or "",
        "fuera_de_rango_curva": bool(asignacion.fuera_de_rango),
        "evaluacion": Evaluacion(evaluacion).label if evaluacion else "",
        "limite": getattr(asignacion, "limite_texto", "") if evaluacion else "",
        "norma": getattr(asignacion, "limite_norma", "") if evaluacion else "",
        "origen_limites": getattr(asignacion, "limite_origen", "") if evaluacion else "",
        "validada": validada,
        "fecha_validacion": fecha(validacion.fecha_validacion) if validada and validacion else "",
    }


@registrar(
    {
        "type": "function",
        "function": {
            "name": "detalle_estudio",
            "description": (
                "Detalle de un estudio: estado y cada prueba con su estado, resultado, unidad, "
                "evaluación (cumple / fuera de norma / sin límite comparable), límite y norma. "
                "Indicá el número de estudio o el N° PI de la muestra."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "numero": {"type": "integer", "description": "Número del estudio."},
                    "numero_pi": {"type": "integer", "description": "N° PI de la muestra."},
                },
            },
        },
    }
)
def detalle_estudio(usuario, numero=None, numero_pi=None):
    from estudios.models import Estudio

    qs = Estudio.objects.select_related("muestra", "muestra__cliente", "muestra__origen")
    if numero is not None:
        estudio = qs.filter(pk=numero).first() if 0 < numero <= MAX_NUMERO_SQL else None
        if estudio is None or not puede_ver(usuario, "estudio", estudio):
            return no_encontrado(f"No hay ningún estudio con el número {numero}.")
        return salida_detalle(usuario, estudio)
    if numero_pi is not None:
        mensaje = f"No hay ninguna muestra con el N° PI {numero_pi}."
        if not 0 < numero_pi <= MAX_NUMERO_SQL:
            return no_encontrado(mensaje)
        estudios = list(qs.filter(muestra__numero_pi=numero_pi).order_by(*Estudio._meta.ordering))
        if not estudios:
            return no_encontrado(mensaje)
        if len(estudios) == 1:
            return salida_detalle(usuario, estudios[0])
        return coincidencias(estudios)
    return no_encontrado("Indicá el número de estudio o el N° PI de la muestra.")


def coincidencias(estudios):
    """Varios estudios: se listan para elegir (FR-007). Se completa en la US2 del asistente."""
    mostrados = estudios[:MAX_LISTA]
    return Salida(
        {
            "encontrado": True,
            "mensaje": "Hay varios estudios que coinciden; pedí cuál.",
            "total": len(estudios),
            "mostrados": len(mostrados),
            "datos": {
                "coincidencias": [
                    {
                        "numero": e.pk,
                        "numero_pi": e.muestra.numero_pi,
                        "origen": e.muestra.origen.nombre,
                        "tipo": e.tipo_nombre_snapshot,
                        "fecha": fecha(e.fecha_creacion),
                        "estado": e.get_estado_display(),
                    }
                    for e in mostrados
                ]
            },
        },
        [referencia_estudio(e) for e in mostrados],
    )


def salida_detalle(usuario, estudio):
    from estudios.views import pruebas_del_detalle

    muestra = estudio.muestra
    con_informe = tiene_informe(estudio)
    datos = {
        "numero": estudio.pk,
        "numero_pi": muestra.numero_pi,
        "cliente": muestra.cliente.nombre_completo,
        "origen": muestra.origen.nombre,
        "tipo": estudio.tipo_nombre_snapshot,
        "estado": estudio.get_estado_display(),
        "fecha_creacion": fecha(estudio.fecha_creacion),
        "tipo_vertido": muestra.get_tipo_vertido_display(),
        "con_informe": con_informe,
        "pruebas": [datos_prueba(a, muestra.tipo_vertido) for a in pruebas_del_detalle(estudio)],
    }
    referencias = [
        referencia_estudio(estudio),
        referencia_muestra(muestra),
        *referencia_cliente(usuario, muestra.cliente),
        *([referencia_informe(estudio)] if con_informe else []),
    ]
    return Salida({"encontrado": True, "datos": datos}, referencias)
