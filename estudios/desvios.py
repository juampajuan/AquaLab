"""Desvíos de un resultado respecto del historial de su origen (US 8.2).

Es la única regla y la única detección de desvíos. El desvío no se guarda: se calcula al vuelo
sobre los resultados calculados y sin validar, cada vez que se muestran (detalle del estudio,
validación y lista «Desvíos sin revisar»), así una carga o una corrección se refleja sola. Nada de
este módulo escribe en la base; la constancia de la revisión la guarda `validar_resultados` en la
`Validacion`.

- Historial: el de la comparación histórica (`comparacion.comparar`, US 8.1); se usan los últimos
  N de `HistorialPrueba.anteriores`.
- Hay desvío si, con al menos N anteriores, el resultado difiere de la mediana de los últimos N en
  más del umbral (%), en cualquier sentido. La mediana y no el promedio: un pico aislado en el
  historial no contamina la comparación. Valores completos y `Decimal`; la comparación se hace sin
  dividir, así exactamente el umbral no es desvío.
- Ausente/Presente: desvío si los últimos N coinciden entre sí y el resultado es el otro estado; la
  referencia es ese valor común (0 o 1).
- La regla (umbral y N) se define solo en `settings.AQUALAB_DESVIOS` y se lee solo con `regla()`.
"""

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from pruebas.limites import limites_aplicables

from . import comparacion
from .comparacion import con_signo, con_unidad, numero, texto_valor
from .mediciones import es_presencia, texto_presencia
from .models import EstadoPruebaEstudio, PruebaEstudio

HISTORIAL_INSUFICIENTE = "historial_insuficiente"


# --- Regla -----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Regla:
    umbral: Decimal  # porcentaje sobre la mediana
    cantidad: int  # resultados validados anteriores cuya mediana es la referencia


def regla():
    """La regla vigente, leída de `settings.AQUALAB_DESVIOS` (único lugar donde se define)."""
    configuracion = getattr(settings, "AQUALAB_DESVIOS", None) or {}
    try:
        umbral = Decimal(str(configuracion["umbral"]))
        cantidad = int(configuracion["cantidad"])
    except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
        raise ImproperlyConfigured(
            "AQUALAB_DESVIOS debe definir «umbral» (porcentaje) y «cantidad» (entero)."
        ) from exc
    if not umbral.is_finite() or umbral <= 0 or cantidad < 1:
        raise ImproperlyConfigured(
            "AQUALAB_DESVIOS: el umbral debe ser mayor que 0 y la cantidad, al menos 1."
        )
    return Regla(umbral, cantidad)


def texto_regla(regla_aplicada):
    """La regla en palabras, con los valores vigentes."""
    if regla_aplicada.cantidad == 1:
        base = "del último resultado validado del origen"
    else:
        cantidad = regla_aplicada.cantidad
        base = f"de la mediana de los últimos {cantidad} resultados validados del origen"
    return f"más de un {numero(regla_aplicada.umbral)} % respecto {base}"


def es_desvio(valor, referencia, umbral):
    """Si `valor` difiere de `referencia` en más de `umbral` % de ella (exacto, sin dividir).
    Con referencia 0, cualquier valor distinto de 0 es desvío."""
    if referencia == 0:
        return valor != 0
    return abs(valor - referencia) * 100 > umbral * abs(referencia)


def mediana(valores):
    """Mediana exacta de valores `Decimal`; con cantidad par, el promedio de los dos centrales."""
    ordenados = sorted(valores)
    medio = len(ordenados) // 2
    if len(ordenados) % 2:
        return ordenados[medio]
    with localcontext() as contexto:
        contexto.prec = 28
        return (ordenados[medio - 1] + ordenados[medio]) / 2


# --- Detección -------------------------------------------------------------------------------


@dataclass(frozen=True)
class Deteccion:
    """Un desvío: el resultado, la referencia (mediana) contra la que se comparó y sus textos.

    La usan los pendientes (con `previos` y `cantidad`) y la constancia de una validación (sin
    previos; `cantidad=0`).
    """

    valor: Decimal
    unidad: str
    referencia: Decimal  # mediana de los últimos N; en Ausente/Presente, el valor común
    diferencia: Decimal
    porcentaje: Decimal | None  # None con referencia 0 o en Ausente/Presente
    texto: str  # el valor como se muestra («< LD», «Ausente»)
    presencia: bool = False
    previos: tuple = ()
    cantidad: int = 0
    umbral: Decimal | None = None

    @property
    def observado(self):
        return self.texto if self.presencia else con_unidad(self.texto, self.unidad)

    @property
    def referencia_texto(self):
        if self.presencia:
            return texto_presencia(self.referencia)
        return con_unidad(numero(self.referencia), self.unidad)

    @property
    def etiqueta_referencia(self):
        if self.presencia:
            return f"Últimos {self.cantidad}" if self.cantidad else "Antes"
        if self.cantidad:
            return f"Mediana de los últimos {self.cantidad}"
        return "Mediana histórica"

    @property
    def flecha(self):
        return "▲" if self.diferencia > 0 else "▼" if self.diferencia < 0 else "="

    @property
    def porcentaje_texto(self):
        if self.porcentaje is None:
            return ""
        return f"{con_signo(str(self.porcentaje).replace('.', ','))} %"

    @property
    def variacion_texto(self):
        if self.presencia:
            antes = f"los últimos {self.cantidad}" if self.cantidad else "antes"
            return f"{self.texto} ({antes}: {texto_presencia(self.referencia)})"
        cantidad = con_unidad(con_signo(numero(self.diferencia)), self.unidad)
        if self.porcentaje is None:
            return f"{self.flecha} {cantidad}, sin porcentaje (mediana previa 0)"
        return f"{self.flecha} {cantidad} ({self.porcentaje_texto})"

    @property
    def umbral_texto(self):
        return "" if self.umbral is None else f"{numero(self.umbral)} %"


def historial_suficiente(historial, regla_aplicada):
    return len(historial.anteriores) >= regla_aplicada.cantidad


def detectar(historial, regla_aplicada):
    """El desvío del resultado de referencia del `historial`, o None si no lo hay (sin
    referencia, con historial insuficiente o dentro del umbral). No consulta la base."""
    actual = historial.referencia
    if actual is None or not historial_suficiente(historial, regla_aplicada):
        return None
    ultimos = tuple(historial.anteriores[-regla_aplicada.cantidad :])
    comunes = dict(
        cantidad=len(ultimos),
        previos=ultimos,
        texto=actual.texto,
        unidad=historial.unidad,
        umbral=regla_aplicada.umbral,
        valor=actual.valor,
    )
    if historial.presencia:
        valores = {p.valor for p in ultimos}
        if len(valores) != 1:
            return None
        (comun,) = valores
        if actual.valor == comun:
            return None
        return Deteccion(
            referencia=comun,
            diferencia=actual.valor - comun,
            porcentaje=None,
            presencia=True,
            **comunes,
        )
    referencia = mediana(p.valor for p in ultimos)
    if not es_desvio(actual.valor, referencia, regla_aplicada.umbral):
        return None
    cambio = comparacion.cambio(actual.valor, referencia, historial.unidad)
    return Deteccion(
        referencia=referencia,
        diferencia=cambio.diferencia,
        porcentaje=cambio.porcentaje,
        **comunes,
    )


def evaluar_estudio(estudio, asignaciones, regla_aplicada=None):
    """`{asignacion.pk: Deteccion | None | HISTORIAL_INSUFICIENTE}` para las `asignaciones` del
    estudio que tienen resultado (las demás no aparecen). Una sola llamada a `comparar`; no
    escribe nada."""
    regla_aplicada = regla_aplicada or regla()
    con_resultado = [a for a in asignaciones if hasattr(a, "resultado")]
    if not con_resultado:
        return {}
    historiales = comparacion.comparar(
        estudio.muestra.origen,
        estudio=estudio,
        codigos={a.prueba.codigo for a in con_resultado},
    )
    por_codigo = {h.prueba.codigo: h for h in historiales}
    evaluacion = {}
    for asignacion in con_resultado:
        historial = por_codigo.get(asignacion.prueba.codigo)
        if historial is None or historial.referencia is None:
            continue
        if historial_suficiente(historial, regla_aplicada):
            evaluacion[asignacion.pk] = detectar(historial, regla_aplicada)
        else:
            evaluacion[asignacion.pk] = HISTORIAL_INSUFICIENTE
    return evaluacion


def constancia(asignacion, validacion, tipo_vertido):
    """La `Deteccion` guardada en una validación con desvío (mediana y umbral de ese momento)."""
    resultado = asignacion.resultado
    presencia = es_presencia(resultado.unidad)
    cambio = comparacion.cambio(resultado.valor, validacion.desvio_referencia, resultado.unidad)
    return Deteccion(
        valor=resultado.valor,
        unidad=resultado.unidad,
        referencia=validacion.desvio_referencia,
        diferencia=cambio.diferencia,
        porcentaje=None if presencia else cambio.porcentaje,
        texto=texto_valor(
            resultado.valor, resultado.unidad, limites_aplicables(asignacion.prueba, tipo_vertido)
        ),
        presencia=presencia,
        umbral=validacion.desvio_umbral,
    )


# --- Pendientes ------------------------------------------------------------------------------


@dataclass(frozen=True)
class Pendiente:
    """Una fila de «Desvíos sin revisar»: un resultado sin validar con desvío."""

    asignacion: PruebaEstudio
    deteccion: Deteccion

    @property
    def estudio(self):
        return self.asignacion.estudio

    @property
    def muestra(self):
        return self.asignacion.estudio.muestra

    @property
    def prueba(self):
        return self.asignacion.prueba

    @property
    def fecha_calculo(self):
        return self.asignacion.resultado.fecha_calculo

    @property
    def enlace_comparacion(self):
        return enlace_comparacion(self.estudio, self.prueba.codigo)


def pendientes(regla_aplicada=None):
    """Los resultados sin validar con desvío de todos los estudios, del calculado más
    recientemente al más antiguo. Una llamada a `comparar` por estudio con pendientes."""
    regla_aplicada = regla_aplicada or regla()
    asignaciones = PruebaEstudio.objects.filter(
        estado=EstadoPruebaEstudio.CARGADA, resultado__isnull=False
    ).select_related("prueba", "resultado", "estudio__muestra__cliente", "estudio__muestra__origen")
    por_estudio = defaultdict(list)
    for asignacion in asignaciones:
        por_estudio[asignacion.estudio_id].append(asignacion)
    filas = []
    for lista in por_estudio.values():
        evaluacion = evaluar_estudio(lista[0].estudio, lista, regla_aplicada)
        for asignacion in lista:
            deteccion = evaluacion.get(asignacion.pk)
            if isinstance(deteccion, Deteccion):
                filas.append(Pendiente(asignacion, deteccion))
    filas.sort(key=lambda f: (f.fecha_calculo, f.asignacion.pk), reverse=True)
    return filas


def enlace_comparacion(estudio, codigo):
    """La comparación histórica (US 8.1) del estudio con solo esa prueba elegida."""
    parametros = urlencode({"estudio": estudio.pk, "pruebas": codigo, "elegir": 1})
    return f"{reverse('estudios:comparacion')}?{parametros}"
