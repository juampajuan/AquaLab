"""Historial de resultados validados de un origen y su variación (US 8.1).

Es la única definición del historial y de la variación: la usa la pantalla de comparación
histórica y la usa la US 8.2 (desvíos). No modifica nada. Los valores se comparan completos (no
redondeados) y siempre con `Decimal`.

- Historial de una prueba: resultados de asignaciones Completadas (⇔ validación vigente, US 6.4)
  de muestras del origen, sin el estudio de referencia, ordenados por fecha de muestreo, N° PI y
  estudio.
- Último: el resultado del estudio de referencia (validado o no) o, sin estudio, el validado más
  reciente. Anteriores: los validados de muestras previas a la del último, con su misma unidad.
"""

import decimal
from collections import defaultdict
from dataclasses import dataclass, field, replace
from decimal import ROUND_HALF_UP, Decimal

from muestras.models import TipoVertido
from pruebas.limites import (
    AUSENTE,
    NO_COMPARABLE,
    Evaluacion,
    bajo_deteccion,
    evaluar,
    leer_limite,
    limites_aplicables,
)
from pruebas.models import Prueba

from .mediciones import es_presencia, texto_presencia
from .models import EstadoPruebaEstudio, Resultado, validaciones_vigentes

SIN_LIMITE_COMPARABLE = "Sin límite comparable"


# --- Textos ----------------------------------------------------------------------------------


def numero(valor):
    """Hasta 4 decimales, sin ceros finales y con coma (la regla de `Resultado.valor_mostrado`)."""
    redondeado = valor.quantize(Decimal("0.0001"), ROUND_HALF_UP).normalize()
    if not redondeado:
        return "0"
    if redondeado.as_tuple().exponent > 0:
        redondeado = redondeado.quantize(Decimal(1))
    return str(redondeado).replace(".", ",")


def con_unidad(texto, unidad):
    unidad = (unidad or "").strip()
    return texto if unidad in ("", "--") else f"{texto} {unidad}"


def con_signo(texto):
    return texto if texto.startswith("-") or texto in ("0", "0,0") else f"+{texto}"


def texto_valor(valor, unidad, limites):
    """«Ausente»/«Presente», «< LD» o el valor como en el resto de la app (como el informe)."""
    if es_presencia(unidad):
        return texto_presencia(valor)
    if bajo_deteccion(valor, limites):
        return f"< {limites.deteccion.strip().replace('.', ',')}"
    return numero(valor)


# --- Estructuras -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Punto:
    """Un resultado del gráfico y de la tabla «Ver datos»."""

    fecha_muestreo: object
    numero_pi: int
    muestra_pk: int
    estudio_pk: int
    valor: Decimal
    texto: str
    unidad: str
    tipo_vertido: str
    validado: bool
    evaluacion: Evaluacion
    es_referencia: bool = False
    otra_unidad: bool = False

    @property
    def muestreo(self):
        """La muestra en el tiempo: lo que define qué resultados son anteriores."""
        return (self.fecha_muestreo, self.numero_pi)

    @property
    def orden(self):
        return (self.fecha_muestreo, self.numero_pi, self.estudio_pk)


@dataclass(frozen=True)
class Franja:
    """Límites permitidos que se dibujan, con los textos del catálogo ya leídos."""

    limites: object  # LimitesAplicables
    minimo: Decimal | None
    maximo: Decimal | None
    presencia: bool
    comparable: bool
    texto: str


@dataclass(frozen=True)
class Cambio:
    diferencia: Decimal
    porcentaje: Decimal | None  # None si la base es 0
    flecha: str
    texto: str


@dataclass(frozen=True)
class Variacion:
    ultimo: Punto
    anterior: Punto
    cantidad_anteriores: int
    promedio: Decimal | None = None
    promedio_texto: str = ""
    contra_anterior: Cambio | None = None
    contra_promedio: Cambio | None = None
    cambio_presencia: str | None = None
    presentes: int | None = None


@dataclass(frozen=True)
class HistorialPrueba:
    prueba: Prueba
    presencia: bool
    unidad: str
    puntos: list = field(default_factory=list)
    referencia: Punto | None = None
    sin_resultado: bool = False
    tiene_historial: bool = False
    franja: Franja | None = None
    variacion: Variacion | None = None
    fuera_de_franja: bool = False
    # Validados de muestras previas a la del último, misma unidad, en orden; los usa la US 8.2.
    anteriores: tuple = ()

    @property
    def validados(self):
        """Los puntos que se dibujan como historial (sin la referencia ni otra unidad)."""
        return [p for p in self.puntos if not p.es_referencia and not p.otra_unidad]


# --- Franja ----------------------------------------------------------------------------------


def nombre_limites(origen_limites):
    if origen_limites == "general":
        return "Límite general"
    return f"Vertido {dict(TipoVertido.choices).get(origen_limites, origen_limites).lower()}"


def franja(prueba, tipo_vertido):
    """La franja de los límites aplicables a una muestra con ese tipo de vertido (US 6.4)."""
    limites = limites_aplicables(prueba, tipo_vertido)
    minimo, maximo = leer_limite(limites.minimo), leer_limite(limites.maximo)
    if NO_COMPARABLE in (minimo, maximo) or (minimo is None and maximo is None):
        return Franja(limites, None, None, False, False, SIN_LIMITE_COMPARABLE)
    origen = nombre_limites(limites.origen)
    if AUSENTE in (minimo, maximo):
        return Franja(limites, None, None, True, True, f"Ausente · {origen}")
    if minimo is not None and maximo is not None:
        texto = f"Entre {numero(minimo)} y {con_unidad(numero(maximo), prueba.unidad)}"
    elif maximo is not None:
        texto = f"Máximo {con_unidad(numero(maximo), prueba.unidad)}"
    else:
        texto = f"Mínimo {con_unidad(numero(minimo), prueba.unidad)}"
    return Franja(limites, minimo, maximo, False, True, f"{texto} · {origen}")


# --- Variación -------------------------------------------------------------------------------


def cambio(ultimo, base, unidad):
    with decimal.localcontext() as contexto:
        contexto.prec = 28
        diferencia = ultimo - base
        porcentaje = None
        if base != 0:
            porcentaje = (diferencia / base * 100).quantize(Decimal("0.1"), ROUND_HALF_UP)
            if porcentaje == 0:
                porcentaje = Decimal("0.0")  # sin «-0,0»
    flecha = "▲" if diferencia > 0 else "▼" if diferencia < 0 else "="
    texto = con_unidad(con_signo(numero(diferencia)), unidad)
    if porcentaje is None:
        texto += " (sin porcentaje: valor previo 0)"
    else:
        texto += f" ({con_signo(str(porcentaje).replace('.', ','))} %)"
    return Cambio(diferencia, porcentaje, flecha, texto)


def variacion(ultimo, anteriores, *, presencia=False, unidad=""):
    """Variación del `ultimo` contra el último de `anteriores` y contra su promedio; `None` sin
    anteriores. En las pruebas Ausente/Presente, cambio de estado y cantidad de Presente."""
    if not anteriores:
        return None
    anterior = anteriores[-1]
    if presencia:
        antes, ahora = texto_presencia(anterior.valor), texto_presencia(ultimo.valor)
        texto = f"Sin cambios ({ahora})" if antes == ahora else f"Cambió: {antes} → {ahora}"
        return Variacion(
            ultimo,
            anterior,
            len(anteriores),
            cambio_presencia=texto,
            presentes=sum(1 for p in anteriores if p.valor == 1),
        )
    with decimal.localcontext() as contexto:
        contexto.prec = 28
        promedio = sum((p.valor for p in anteriores), Decimal(0)) / len(anteriores)
    return Variacion(
        ultimo,
        anterior,
        len(anteriores),
        promedio=promedio,
        promedio_texto=con_unidad(numero(promedio), unidad),
        contra_anterior=cambio(ultimo.valor, anterior.valor, unidad),
        contra_promedio=cambio(ultimo.valor, promedio, unidad),
    )


# --- Consulta --------------------------------------------------------------------------------


def evaluacion_de(asignacion, valor, tipo_vertido):
    """La evaluación guardada al validar; sin validación vigente, la del catálogo (US 6.4)."""
    vigentes = getattr(asignacion, "validaciones_vigentes", [])
    if vigentes and asignacion.estado == EstadoPruebaEstudio.COMPLETADA:
        return Evaluacion(vigentes[0].evaluacion)
    return evaluar(valor, limites_aplicables(asignacion.prueba, tipo_vertido))


def punto_de(asignacion, resultado, muestra, *, es_referencia=False):
    limites = limites_aplicables(asignacion.prueba, muestra.tipo_vertido)
    return Punto(
        fecha_muestreo=muestra.fecha_muestreo,
        numero_pi=muestra.numero_pi,
        muestra_pk=muestra.pk,
        estudio_pk=asignacion.estudio_id,
        valor=resultado.valor,
        texto=texto_valor(resultado.valor, resultado.unidad, limites),
        unidad=resultado.unidad,
        tipo_vertido=muestra.tipo_vertido,
        validado=asignacion.estado == EstadoPruebaEstudio.COMPLETADA,
        evaluacion=evaluacion_de(asignacion, resultado.valor, muestra.tipo_vertido),
        es_referencia=es_referencia,
    )


def asignaciones_de(estudio):
    return list(
        estudio.pruebas_asignadas.select_related("prueba", "resultado")
        .prefetch_related("prueba__limites_vertido", validaciones_vigentes())
        .order_by("prueba__codigo", "pk")
    )


def pruebas_disponibles(origen, estudio=None):
    """Las pruebas del estudio (por código) o, sin estudio, las que tienen algún resultado
    validado en el origen (por nombre) (FR-013)."""
    if estudio is not None:
        return [
            a.prueba
            for a in estudio.pruebas_asignadas.select_related("prueba").order_by(
                "prueba__codigo", "pk"
            )
        ]
    pruebas = Prueba.objects.filter(
        pruebaestudio__estado=EstadoPruebaEstudio.COMPLETADA,
        pruebaestudio__estudio__muestra__origen=origen,
    ).distinct()
    return sorted(pruebas, key=lambda p: (p.nombre.casefold(), p.codigo))


def comparar(origen, *, estudio=None, codigos=None):
    """El historial de cada prueba del origen, con el `estudio` como referencia si se da.

    Las pruebas son las del estudio o, sin él, las que tienen algún validado en el origen;
    `codigos` las limita. Hace una cantidad fija de consultas.
    """
    if estudio is not None and estudio.muestra.origen_id != origen.pk:
        raise ValueError("El estudio no es del origen que se compara.")
    referencia = {}
    if estudio is not None:
        for asignacion in asignaciones_de(estudio):
            if codigos is None or asignacion.prueba.codigo in codigos:
                referencia.setdefault(asignacion.prueba.codigo, asignacion)

    resultados = (
        Resultado.objects.filter(
            asignacion__estado=EstadoPruebaEstudio.COMPLETADA,
            asignacion__estudio__muestra__origen=origen,
        )
        .select_related("asignacion__estudio__muestra", "asignacion__prueba")
        .prefetch_related(
            "asignacion__prueba__limites_vertido", validaciones_vigentes("asignacion__")
        )
    )
    if estudio is not None:
        resultados = resultados.exclude(asignacion__estudio=estudio).filter(
            asignacion__prueba__codigo__in=list(referencia)
        )
    elif codigos is not None:
        resultados = resultados.filter(asignacion__prueba__codigo__in=list(codigos))

    historia = defaultdict(list)
    pruebas = {}
    for resultado in resultados:
        asignacion = resultado.asignacion
        historia[asignacion.prueba.codigo].append(
            punto_de(asignacion, resultado, asignacion.estudio.muestra)
        )
        pruebas.setdefault(asignacion.prueba.codigo, asignacion.prueba)

    if estudio is not None:
        orden = list(referencia)
        pruebas.update({c: a.prueba for c, a in referencia.items()})
    else:
        orden = sorted(pruebas, key=lambda c: (pruebas[c].nombre.casefold(), c))
    return [
        historial_de_prueba(pruebas[codigo], historia[codigo], referencia.get(codigo), estudio)
        for codigo in orden
    ]


def historial_de_prueba(prueba, puntos, asignacion_ref, estudio):
    ref = None
    if asignacion_ref is not None and hasattr(asignacion_ref, "resultado"):
        ref = punto_de(
            asignacion_ref, asignacion_ref.resultado, estudio.muestra, es_referencia=True
        )
    puntos = sorted(puntos, key=lambda p: p.orden)
    unidad = ref.unidad if ref else (puntos[-1].unidad if puntos else prueba.unidad)
    puntos = [replace(p, otra_unidad=p.unidad.strip() != unidad.strip()) for p in puntos]
    validos = [p for p in puntos if not p.otra_unidad]
    ultimo = ref or (validos[-1] if validos else None)

    if estudio is not None:
        tipo_vertido = estudio.muestra.tipo_vertido
    elif ultimo is not None:
        tipo_vertido = ultimo.tipo_vertido
    else:
        tipo_vertido = puntos[-1].tipo_vertido if puntos else TipoVertido.AGUA

    presencia = es_presencia(unidad)
    anteriores = [p for p in validos if p.muestreo < ultimo.muestreo] if ultimo is not None else []
    return HistorialPrueba(
        prueba=prueba,
        presencia=presencia,
        unidad=unidad,
        puntos=sorted([*puntos, *([ref] if ref else [])], key=lambda p: p.orden),
        referencia=ref,
        sin_resultado=estudio is not None and ref is None,
        tiene_historial=bool(validos),
        franja=franja(prueba, tipo_vertido),
        variacion=(
            variacion(ultimo, anteriores, presencia=presencia, unidad=unidad) if ultimo else None
        ),
        fuera_de_franja=ultimo is not None and ultimo.evaluacion == Evaluacion.FUERA_DE_NORMA,
        anteriores=tuple(anteriores),
    )
