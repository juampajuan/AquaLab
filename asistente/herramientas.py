"""Herramientas de solo lectura que el asistente ofrece al modelo (contracts/herramientas.md).

Se ejecutan con el usuario que pregunta, dentro de una transacción `READ ONLY` que además siempre
se deshace (research R6): una escritura falla y nada queda en la base. Las salidas solo llevan los
campos de la lista blanca (data-model.md); las referencias para los enlaces quedan en AquaLab y no
se mandan al modelo. Cada historia registra sus herramientas con `@registrar`.
"""

import json
import logging
from dataclasses import dataclass, field, replace

from django.db import connection, transaction

from pruebas.limites import Evaluacion

logger = logging.getLogger("asistente")

PEDIDO_INVALIDO = {"encontrado": False, "mensaje": "Pedido inválido."}
NO_SE_PUDO = {"encontrado": False, "mensaje": "No se pudo consultar."}

TIPOS_JSON = {
    "string": (str,),
    "integer": (int,),
    "boolean": (bool,),
    "null": (type(None),),
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
    # Coincidencias para elegir: `Referencia` con `pregunta` (T053).
    opciones: list = field(default_factory=list)


@dataclass
class Ejecucion:
    salida: dict
    referencias: list = field(default_factory=list)
    # Herramienta conocida con argumentos válidos (research R3: si ninguna lo fue, mensaje fijo).
    valida: bool = True
    avisos: list = field(default_factory=list)
    primeras: list = field(default_factory=list)
    opciones: list = field(default_factory=list)


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
        # El tipo puede ser una lista, como ["string", "null"] (US 10.3).
        tipo = propiedades[nombre].get("type")
        nombres = tipo if isinstance(tipo, list) else [tipo]
        if any(n not in TIPOS_JSON for n in nombres):
            tipos = (object,)
        else:
            tipos = tuple(t for n in nombres for t in TIPOS_JSON[n])
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
        opciones=list(resultado.opciones),
    )


def puede_ver(usuario, tipo, objeto=None):
    """Única regla de permisos del asistente (research R5): lo mismo que las pantallas. Hoy
    muestras, estudios e informes los ve cualquier empleado con sesión; la ficha y el historial de
    un cliente inactivo se rechazan."""
    if usuario is None or not usuario.is_authenticated or not usuario.is_active:
        return False
    if tipo in ("cliente", "historial"):
        return bool(objeto is None or objeto.activo)
    # "registro" (US 10.3): lo mismo que exigen hoy muestras:registrar y estudios:crear (solo la
    # sesión). Si esas pantallas suman un permiso, agregarlo acá también (research R8).
    return True


def datos_cliente(cliente):
    """Lista blanca de un cliente: nunca correo, teléfono, domicilio ni documento (FR-014)."""
    return {"nombre": cliente.nombre_completo, "activo": cliente.activo}


# --- Consultas (cada una replica la consulta de su pantalla, research R4) ---

FORMATO_FECHA = "%d/%m/%Y"
ESTUDIOS_POR_MUESTRA = 5  # una vuelta para la muestra y una por estudio (max_vueltas − 1)
MAX_LISTA = 10
MAX_NUMERO_SQL = 2_147_483_647
CUMPLE = Evaluacion.CUMPLE.label
FUERA_DE_NORMA = Evaluacion.FUERA_DE_NORMA.label
SIN_LIMITE = Evaluacion.SIN_LIMITE.label


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
    etiqueta = f"{muestra.nombre} (PI {numero})" if muestra.nombre else f"PI {numero}"
    return Referencia("muestra", muestra.pk, etiqueta, claves=(f"PI {numero}", numero))


def referencia_estudio(estudio):
    from .enlaces import Referencia

    numero = estudio.pk
    return Referencia(
        "estudio",
        numero,
        f"Estudio {numero}",
        claves=(f"Estudio {numero}", f"Estudio N° {numero}", f"Estudio Nº {numero}"),
        patron=patron_estudio(numero),
    )


# Formas de numerar que usa el modelo, sobre el texto normalizado (la «º» queda como «o»):
# «n.º», «n°», «nº», «nro.», «número» y «#». Sin la palabra «estudio» solo valen las que no se
# confunden con texto común («n.º 42», «n° 42», «número 42», «#42»): «N° PI 42» no es un estudio
# y solo se enlazan estudios que una herramienta devolvió en esa pregunta.
NUMERADORES = r"(?:n\.?\s*[o°]\.?|nro\.?|numero|#)"
NUMERADORES_SUELTOS = r"(?:n\.\s*[o°]\.?|n°|nro\.?|numero|#)"


def patron_estudio(numero):
    return rf"(?<!\w)(?:estudio\s*(?:{NUMERADORES}\s*)?|{NUMERADORES_SUELTOS}\s*){numero}(?!\w)"


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
                "recientes, cada uno con sus pruebas (código, estado, resultado y evaluación); "
                "para unidades, límites y normas usá detalle_estudio."
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
                    **dict(zip(("pruebas", "resumen"), pruebas_resumidas(e, muestra), strict=True)),
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
        opciones=[
            replace(
                referencia_muestra(m),
                etiqueta=f"¿Cómo está «{m.nombre}»?",
                pregunta=f"¿Cómo está el PI {m.numero_pi}?",
            )
            for m in muestras
        ],
    )


CAMPOS_RESUMIDOS = ("codigo", "nombre", "estado", "resultado", "unidad", "evaluacion")


def pruebas_resumidas(estudio, muestra):
    """Las pruebas del estudio con 6 campos (cuidan la cuota de tokens) y el resumen que cuenta
    AquaLab (el modelo no cuenta): los mismos valores que `detalle_estudio`, que agrega límite y
    norma."""
    from estudios.views import pruebas_del_detalle

    estudio.muestra = muestra
    completas = [datos_prueba(a, muestra.tipo_vertido) for a in pruebas_del_detalle(estudio)]
    pruebas = [{campo: prueba[campo] for campo in CAMPOS_RESUMIDOS} for prueba in completas]
    resumen = {
        "cumple": sum(1 for p in completas if p["evaluacion"] == CUMPLE),
        "fuera_de_norma": sum(1 for p in completas if p["evaluacion"] == FUERA_DE_NORMA),
        "sin_limite_comparable": sum(1 for p in completas if p["evaluacion"] == SIN_LIMITE),
        "sin_resultado": sum(1 for p in completas if not p["resultado"]),
    }
    return pruebas, resumen


def datos_muestra(muestra):
    """Lista blanca de una muestra (data-model.md): sin responsable ni quién la registró, y sin el
    estado de la muestra (SCRUM-82 lo sacó de la ficha)."""
    return {
        "numero_pi": muestra.numero_pi,
        "nombre": muestra.nombre,
        "cliente": muestra.cliente.nombre_completo,
        "origen": muestra.origen.nombre,
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
                "Indicá el número de estudio, el N° PI de la muestra o un texto (muestra, origen, "
                "cliente o tipo de estudio). Si hay varias coincidencias, devuelve la lista para "
                "elegir. Para «qué no cumple», pasá solo_fuera_de_norma=true."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "numero": {"type": "integer", "description": "Número del estudio."},
                    "numero_pi": {"type": "integer", "description": "N° PI de la muestra."},
                    "texto": {
                        "type": "string",
                        "description": "Muestra, origen, cliente o tipo de estudio.",
                    },
                    "solo_fuera_de_norma": {
                        "type": "boolean",
                        "description": "Solo las pruebas fuera de norma, con un resumen.",
                    },
                },
            },
        },
    }
)
def detalle_estudio(usuario, numero=None, numero_pi=None, texto=None, solo_fuera_de_norma=False):
    from django.db.models import Q

    from estudios.busqueda import filtro_busqueda
    from estudios.models import Estudio

    if not puede_ver(usuario, "estudio"):
        return no_encontrado("No se pudo consultar.")
    qs = Estudio.objects.select_related("muestra", "muestra__cliente", "muestra__origen").order_by(
        *Estudio._meta.ordering
    )
    if numero is not None:
        estudio = qs.filter(pk=numero).first() if 0 < numero <= MAX_NUMERO_SQL else None
        if estudio is None:
            return no_encontrado(f"No hay ningún estudio con el número {numero}.")
        return salida_detalle(usuario, estudio, solo_fuera_de_norma)
    if numero_pi is not None:
        if not 0 < numero_pi <= MAX_NUMERO_SQL:
            return no_encontrado(f"No hay ninguna muestra con el N° PI {numero_pi}.")
        elegidos = qs.filter(muestra__numero_pi=numero_pi)
        sin_coincidencias = f"No hay ninguna muestra con el N° PI {numero_pi}."
    elif (texto or "").strip():
        texto = texto.strip()
        # La búsqueda de estudios (US 5.2) más el origen («la escuela N° 12», research R4).
        elegidos = qs.filter(
            filtro_busqueda(texto) | Q(muestra__origen__nombre__unaccent__icontains=texto)
        )
        sin_coincidencias = f"No hay estudios que coincidan con «{texto}»."
    else:
        return no_encontrado("Indicá el número de estudio, el N° PI de la muestra o un texto.")
    total = elegidos.count()
    if not total:
        return no_encontrado(sin_coincidencias)
    if total == 1:
        return salida_detalle(usuario, elegidos.get(), solo_fuera_de_norma)
    return coincidencias(list(elegidos[:MAX_LISTA]), total, solo_fuera_de_norma)


def coincidencias(mostrados, total, solo_fuera_de_norma=False):
    """Varios estudios: se listan para elegir, más recientes primero (FR-007). Cada uno es una
    opción con la pregunta de seguimiento que corresponde a lo que se preguntó."""
    plantilla = (
        "¿Qué no cumple en el estudio {}?" if solo_fuera_de_norma else "¿Cómo está el estudio {}?"
    )
    return Salida(
        {
            "encontrado": True,
            "mensaje": "Hay varios estudios que coinciden; pedí cuál.",
            "total": total,
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
        opciones=[
            replace(referencia_estudio(e), pregunta=plantilla.format(e.pk)) for e in mostrados
        ],
    )


def salida_detalle(usuario, estudio, solo_fuera_de_norma=False):
    from estudios.views import pruebas_del_detalle

    muestra = estudio.muestra
    con_informe = tiene_informe(estudio)
    pruebas = [datos_prueba(a, muestra.tipo_vertido) for a in pruebas_del_detalle(estudio)]
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
        "pruebas": pruebas,
    }
    if solo_fuera_de_norma:
        datos["pruebas"] = [p for p in pruebas if p["evaluacion"] == FUERA_DE_NORMA]
        datos["resumen"] = {
            "sin_resultado": sum(1 for p in pruebas if not p["resultado"]),
            "sin_limite_comparable": sum(1 for p in pruebas if p["evaluacion"] == SIN_LIMITE),
            "total": len(pruebas),
        }
    referencias = [
        referencia_estudio(estudio),
        referencia_muestra(muestra),
        *referencia_cliente(usuario, muestra.cliente),
        *([referencia_informe(estudio)] if con_informe else []),
    ]
    return Salida({"encontrado": True, "datos": datos}, referencias)


# --- Clientes (US3) ---


def referencia_historial(cliente):
    from .enlaces import Referencia

    return Referencia(
        "historial",
        cliente.pk,
        f"Historial de {cliente.nombre_completo}",
        claves=(f"Historial de {cliente.nombre_completo}", "historial"),
    )


def referencias_del_cliente(usuario, cliente):
    if not puede_ver(usuario, "cliente", cliente):
        return []
    return [*referencia_cliente(usuario, cliente), referencia_historial(cliente)]


def datos_cliente_con_id(cliente):
    return {"id": cliente.pk, **datos_cliente(cliente)}


def opciones_de_clientes(usuario, clientes):
    """Cada cliente que se puede abrir es una opción «¿Qué estudios tiene…?» (T053)."""
    return [
        replace(
            r,
            etiqueta=f"¿Qué estudios tiene {c.nombre_completo}?",
            pregunta=f"¿Qué estudios tiene {c.nombre_completo}?",
        )
        for c in clientes
        for r in referencia_cliente(usuario, c)
    ]


@registrar(
    {
        "type": "function",
        "function": {
            "name": "buscar_cliente",
            "description": (
                "Busca clientes por nombre, razón social o número de documento. Devuelve su "
                "identificador, nombre y si está activo (nunca datos de contacto)."
            ),
            "parameters": {
                "type": "object",
                "properties": {"texto": {"type": "string", "description": "Nombre del cliente."}},
                "required": ["texto"],
            },
        },
    }
)
def buscar_cliente(usuario, texto):
    from clientes.models import Cliente
    from clientes.views import buscar_clientes, filtro_clientes

    texto = texto.strip()
    if not texto or not puede_ver(usuario, "busqueda"):
        return no_encontrado("Indicá el nombre del cliente.")
    activos = list(buscar_clientes(texto)[:MAX_LISTA])
    inactivos = list(
        Cliente.objects.filter(filtro_clientes(texto), activo=False).order_by(
            *Cliente._meta.ordering
        )[: MAX_LISTA - len(activos)]
    )
    clientes = activos + inactivos
    if not clientes:
        return no_encontrado(f"No hay clientes que coincidan con «{texto}».")
    return Salida(
        {"encontrado": True, "datos": {"clientes": [datos_cliente_con_id(c) for c in clientes]}},
        [r for c in clientes for r in referencias_del_cliente(usuario, c)],
        opciones=opciones_de_clientes(usuario, clientes),
    )


@registrar(
    {
        "type": "function",
        "function": {
            "name": "estudios_de_cliente",
            "description": (
                "Estudios más recientes de un cliente, en el orden de su historial: N° PI, origen, "
                "tipo, fecha de ingreso y estado. Indicá el nombre del cliente o el id que "
                "devolvió buscar_cliente."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente": {"type": "string", "description": "Nombre o razón social."},
                    "cliente_id": {"type": "integer", "description": "Id de buscar_cliente."},
                },
            },
        },
    }
)
def estudios_de_cliente(usuario, cliente=None, cliente_id=None):
    from clientes.historial import muestras_del_historial
    from clientes.models import Cliente
    from clientes.views import filtro_clientes
    from estudios.models import Estudio

    if not puede_ver(usuario, "busqueda"):
        return no_encontrado("No se pudo consultar.")
    if cliente_id is not None:
        elegido = (
            Cliente.objects.filter(pk=cliente_id).first()
            if 0 < cliente_id <= MAX_NUMERO_SQL
            else None
        )
        if elegido is None:
            return no_encontrado("No hay ningún cliente con ese identificador.")
    elif (cliente or "").strip():
        texto = cliente.strip()
        encontrados = list(
            Cliente.objects.filter(filtro_clientes(texto)).order_by(*Cliente._meta.ordering)[
                : MAX_LISTA + 1
            ]
        )
        if not encontrados:
            return no_encontrado(f"No hay ningún cliente que coincida con «{texto}».")
        if len(encontrados) > 1:
            mostrados = encontrados[:MAX_LISTA]
            return Salida(
                {
                    "encontrado": True,
                    "mensaje": "Hay varios clientes con ese nombre; pedí cuál.",
                    "datos": {"coincidencias": [datos_cliente_con_id(c) for c in mostrados]},
                },
                [r for c in mostrados for r in referencias_del_cliente(usuario, c)],
                opciones=opciones_de_clientes(usuario, mostrados),
            )
        elegido = encontrados[0]
    else:
        return no_encontrado("Indicá el nombre del cliente.")
    # La ficha y el historial de un cliente inactivo no se abren (US 3.3): tampoco acá.
    if not puede_ver(usuario, "historial", elegido):
        return no_encontrado(f"El cliente {elegido.nombre_completo} está inactivo.")
    total = Estudio.objects.filter(muestra__cliente=elegido).count()
    estudios = []
    for muestra in muestras_del_historial(elegido):
        for estudio in muestra.estudios_historial:
            estudios.append((muestra, estudio))
            if len(estudios) == MAX_LISTA:
                break
        if len(estudios) == MAX_LISTA:
            break
    datos = {
        "cliente": elegido.nombre_completo,
        "estudios": [
            {
                "numero": estudio.pk,
                "numero_pi": muestra.numero_pi,
                "origen": muestra.origen.nombre,
                "tipo": estudio.tipo_nombre_snapshot,
                "fecha_ingreso": fecha(muestra.fecha_ingreso),
                "estado": estudio.get_estado_display(),
                "con_informe": tiene_informe(estudio),
            }
            for muestra, estudio in estudios
        ],
    }
    referencias = referencias_del_cliente(usuario, elegido)
    for muestra, estudio in estudios:
        referencias.append(referencia_muestra(muestra))
        referencias.append(referencia_estudio(estudio))
        if tiene_informe(estudio):
            referencias.append(referencia_informe(estudio))
    avisos, primeras = [], []
    if total > len(estudios):
        avisos.append(
            f"{elegido.nombre_completo} tiene {total} estudios; se muestran los "
            f"{len(estudios)} más recientes. El resto está en su historial."
        )
        primeras.append(referencia_historial(elegido))
    return Salida(
        {"encontrado": True, "total": total, "mostrados": len(estudios), "datos": datos},
        referencias,
        avisos,
        primeras,
    )


# Herramientas de la US 10.3 (preparar el registro de una muestra o un estudio). Al final para
# que `registro` encuentre definido todo lo que importa de este módulo.
from . import registro  # noqa: E402, F401
