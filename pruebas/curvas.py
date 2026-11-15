"""Curvas de calibración de las pruebas por absorbancia (US 6.6).

Única fuente de las reglas de curvas: la recta, qué curva usa cada resultado, el aviso de fuera de
rango, las mediciones que esperan curva y las operaciones de guardar y borrar. El cálculo de los
resultados sigue siendo solo `estudios/calculo.py`.

Orden de bloqueos (research R5): estudios (por pk) → lock de la prueba → `Prueba` o curva. Guardar
y borrar toman el lock exclusivo; las cargas, el compartido antes de leer la vigente.
"""

import datetime
import uuid
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, localcontext

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.utils import timezone

R2_MINIMO = Decimal("0.995")
CLAVE_LOCK_CURVAS = 6_600_001
MINIMO_PUNTOS = 3
MAXIMO_PUNTOS = 50
DECIMALES_RECTA = Decimal("1E-12")
DECIMALES_R2 = Decimal("1E-10")

MENSAJE_POCOS_PUNTOS = "Hacen falta al menos 3 puntos."
MENSAJE_MUCHOS_PUNTOS = "Una curva puede tener hasta 50 puntos."
MENSAJE_FALTA_CONCENTRACION = "Falta la concentración."
MENSAJE_FALTA_ABSORBANCIA = "Falta la absorbancia."
MENSAJE_NEGATIVO = "No puede ser negativa."
MENSAJE_CONCENTRACIONES_IGUALES = (
    "Las concentraciones son todas iguales: no se puede calcular la recta."
)
MENSAJE_ABSORBANCIAS_IGUALES = (
    "Las absorbancias son todas iguales: la recta no permite convertir absorbancia en "
    "concentración."
)
MENSAJE_PENDIENTE_CERO = (
    "La pendiente es cero: la recta no permite convertir absorbancia en concentración."
)
MENSAJE_FECHA_FUTURA = "La fecha de preparación no puede ser posterior a hoy."
MENSAJE_FECHA_INVALIDA = "Ingresá una fecha válida."
MENSAJE_R2_BAJO = "R² menor que 0,995: revisá los puntos antes de guardar"
MENSAJE_BORRADOR_INVALIDO = "La confirmación venció o no es válida. Volvé a cargar la curva."
MENSAJE_FALTA_CURVA = "Falta curva de calibración."
MENSAJE_ANTES_DE_LA_CURVA = "Se cargó antes de la curva vigente."


class CurvaError(Exception):
    """Error de una operación de curvas; el mensaje es el que ve el usuario."""


class CurvaInvalida(CurvaError):
    """Los puntos o los datos no permiten guardar la curva. `errores`: campo o fila → mensaje."""

    def __init__(self, errores):
        self.errores = dict(errores)
        super().__init__(" ".join(str(m) for m in self.errores.values()))


class NoEsPruebaPorCurva(CurvaError):
    def __init__(self):
        super().__init__("Esta prueba no se calcula con curva de calibración.")


class CurvaUsada(CurvaError):
    def __init__(self):
        super().__init__("Esta curva ya se usó en resultados: no se puede borrar.")


def bloquear_prueba(prueba_id, *, compartido=False):
    """Lock de las curvas de una prueba hasta el fin de la transacción (exclusivo o compartido)."""
    funcion = "pg_advisory_xact_lock_shared" if compartido else "pg_advisory_xact_lock"
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT {funcion}(%s, %s)", [CLAVE_LOCK_CURVAS, prueba_id])


def texto_numero(valor, decimales=None):
    """Texto de un Decimal con coma decimal y sin ceros finales (0,499; 0,0012; 12)."""
    if valor is None:
        return ""
    if decimales is not None:
        valor = valor.quantize(decimales, ROUND_HALF_UP)
    valor = valor.normalize()
    if valor.as_tuple().exponent > 0:  # normalize() escribe 80 como 8E+1
        valor = valor.quantize(Decimal(1))
    return f"{valor:f}".replace(".", ",")


# --- Recta ------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Ajuste:
    """Recta absorbancia = pendiente × concentración + ordenada, con lo que se guarda."""

    pendiente: Decimal
    ordenada: Decimal
    r2: Decimal
    concentracion_min: Decimal
    concentracion_max: Decimal
    absorbancia_min: Decimal
    absorbancia_max: Decimal

    @property
    def r2_bajo(self):
        return self.r2 < R2_MINIMO


def ajustar(puntos):
    """Recta por mínimos cuadrados de `puntos` [(concentración, absorbancia)], en `Decimal`.

    Pendiente y ordenada quedan con 12 decimales y R² con 10 (research R2); el resultado de una
    medición se calcula con esos valores guardados. Lanza `CurvaInvalida` si no hay recta útil.
    """
    if len(puntos) < MINIMO_PUNTOS:
        raise CurvaInvalida({"puntos": MENSAJE_POCOS_PUNTOS})
    if len(puntos) > MAXIMO_PUNTOS:
        raise CurvaInvalida({"puntos": MENSAJE_MUCHOS_PUNTOS})
    if any(c < 0 or a < 0 for c, a in puntos):
        raise CurvaInvalida({"puntos": MENSAJE_NEGATIVO})
    concentraciones = [c for c, _ in puntos]
    absorbancias = [a for _, a in puntos]
    if len(set(concentraciones)) < 2:
        raise CurvaInvalida({"puntos": MENSAJE_CONCENTRACIONES_IGUALES})
    if len(set(absorbancias)) < 2:
        raise CurvaInvalida({"puntos": MENSAJE_ABSORBANCIAS_IGUALES})
    with localcontext() as contexto:
        contexto.prec = 40
        n = Decimal(len(puntos))
        sx, sy = sum(concentraciones), sum(absorbancias)
        sxy = sum(c * a for c, a in puntos)
        sxx = sum(c * c for c in concentraciones)
        syy = sum(a * a for a in absorbancias)
        dx, dy, cruzado = n * sxx - sx * sx, n * syy - sy * sy, n * sxy - sx * sy
        pendiente = (cruzado / dx).quantize(DECIMALES_RECTA, ROUND_HALF_UP)
        if not pendiente:
            raise CurvaInvalida({"puntos": MENSAJE_PENDIENTE_CERO})
        ordenada = ((sy - (cruzado / dx) * sx) / n).quantize(DECIMALES_RECTA, ROUND_HALF_UP)
        r2 = (cruzado * cruzado / (dx * dy)).quantize(DECIMALES_R2, ROUND_HALF_UP)
    return Ajuste(
        pendiente=pendiente,
        ordenada=ordenada,
        r2=min(r2, Decimal(1)),
        concentracion_min=min(concentraciones),
        concentracion_max=max(concentraciones),
        absorbancia_min=min(absorbancias),
        absorbancia_max=max(absorbancias),
    )


def leer_puntos(filas):
    """Puntos [(Decimal, Decimal)] de filas de textos [(concentración, absorbancia)].

    Misma lectura que las mediciones (`leer_valor`: coma o punto, hasta 6 decimales); las filas
    vacías se ignoran. Lanza `CurvaInvalida` con el error de la primera fila con problemas.
    """
    from estudios.mediciones import leer_valor

    if not isinstance(filas, (list, tuple)):
        raise CurvaInvalida({"puntos": MENSAJE_POCOS_PUNTOS})
    puntos = []
    for numero, fila in enumerate(filas, start=1):
        if not isinstance(fila, (list, tuple)) or len(fila) != 2:
            raise CurvaInvalida({"puntos": f"Punto {numero}: los datos no son válidos."})
        textos = [str(v or "").strip() for v in fila]
        if not any(textos):
            continue
        try:
            concentracion, absorbancia = (leer_valor(v) for v in textos)
        except ValidationError as exc:
            raise CurvaInvalida({"puntos": f"Punto {numero}: {' '.join(exc.messages)}"}) from exc
        if concentracion is None:
            raise CurvaInvalida({"puntos": f"Punto {numero}: {MENSAJE_FALTA_CONCENTRACION}"})
        if absorbancia is None:
            raise CurvaInvalida({"puntos": f"Punto {numero}: {MENSAJE_FALTA_ABSORBANCIA}"})
        puntos.append((concentracion, absorbancia))
    return puntos


def leer_fecha(texto):
    try:
        fecha = datetime.date.fromisoformat(str(texto))
    except ValueError as exc:
        raise CurvaInvalida({"fecha_preparacion": MENSAJE_FECHA_INVALIDA}) from exc
    if fecha > timezone.localdate():
        raise CurvaInvalida({"fecha_preparacion": MENSAJE_FECHA_FUTURA})
    return fecha


# --- Lecturas para el cálculo y las pantallas -------------------------------------------------


def es_por_curva(prueba):
    from .models import TipoCalculo

    return prueba.tipo_calculo == TipoCalculo.CURVA


def curva_para(asignacion, *, bloquear=False):
    """La curva con la que se calcula el resultado de una asignación por curva (FR-016, FR-020).

    La del resultado que ya tiene (una corrección o un recálculo usan la misma) o, si no tiene,
    la vigente de la prueba (o None). Con `bloquear=True` toma antes el lock compartido de la
    prueba, así nadie borra la vigente mientras se calcula con ella (research R5).
    """
    resultado = getattr(asignacion, "resultado", None)
    if resultado is not None and resultado.pk and resultado.curva_id:
        return resultado.curva
    if bloquear:
        bloquear_prueba(asignacion.prueba_id, compartido=True)
    return asignacion.prueba.curva_vigente


def fuera_de_rango(asignacion):
    """La absorbancia medida está fuera del rango de los estándares de la curva usada (FR-019).

    Bordes inclusivos: una absorbancia igual a la del estándar más bajo o más alto está dentro.
    """
    resultado = getattr(asignacion, "resultado", None)
    medicion = getattr(asignacion, "medicion", None)
    if resultado is None or medicion is None or not resultado.curva_id:
        return False
    curva = resultado.curva
    return not curva.absorbancia_min <= medicion.valor <= curva.absorbancia_max


def motivo_curva(asignacion):
    """«Se cargó antes de la curva vigente.» si la medición espera curva y ya hay una vigente
    (FR-026); si no, None. Lo consulta primero `calculo.motivo_sin_resultado`."""
    if not es_por_curva(asignacion.prueba):
        return None
    if not hasattr(asignacion, "medicion") or hasattr(asignacion, "resultado"):
        return None
    return MENSAJE_ANTES_DE_LA_CURVA if asignacion.prueba.curva_vigente else None


def pendientes_de_curva(*, prueba=None, estudio=None):
    """Asignaciones de pruebas por curva con medición y sin resultado, en estudios que admiten
    mediciones (Pendiente de análisis o En proceso). Por prueba (al confirmar una curva) o por
    estudio (`Calcular con la curva vigente`, solo las de pruebas con curva vigente)."""
    from estudios.models import EstadoEstudio, PruebaEstudio

    from .models import TipoCalculo

    consulta = PruebaEstudio.objects.filter(
        prueba__tipo_calculo=TipoCalculo.CURVA,
        medicion__isnull=False,
        resultado__isnull=True,
        estudio__estado__in=(EstadoEstudio.PENDIENTE_ANALISIS, EstadoEstudio.EN_PROCESO),
    )
    if prueba is not None:
        consulta = consulta.filter(prueba=prueba)
    if estudio is not None:
        consulta = consulta.filter(estudio=estudio, prueba__curvas__vigente=True)
    return list(consulta.select_related("prueba").order_by("estudio_id", "pk"))


# --- Guardar ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Guardado:
    curva: object
    anterior: object = None
    calculadas: int = 0
    repetida: bool = False


def guardar_curva(*, usuario, prueba_id, datos, clave, calcular_pendientes=False):
    """Guarda una curva nueva como vigente de la prueba; la vigente anterior pasa a histórica.

    `datos`: fecha_preparacion (ISO), observacion, archivo_origen y puntos (textos). Revalida
    todo (el borrador viene de la sesión). Con la misma `clave` devuelve la curva ya guardada.
    """
    from estudios.models import Estudio

    from .gestion import autorizar
    from .models import CurvaCalibracion, Prueba, PuntoCurva, TipoCalculo

    usuario = autorizar(usuario)
    if not isinstance(datos, dict):
        raise CurvaInvalida({"puntos": MENSAJE_POCOS_PUNTOS})
    clave = uuid.UUID(str(clave))
    with transaction.atomic():
        estudios = []
        if calcular_pendientes:
            # Primero los estudios (por pk), después el lock de la prueba: el mismo orden que una
            # carga de mediciones, que bloquea el estudio y después toma el lock compartido.
            ids = sorted({a.estudio_id for a in pendientes_de_curva(prueba=prueba_id)})
            estudios = list(Estudio.objects.select_for_update().filter(pk__in=ids).order_by("pk"))
        bloquear_prueba(prueba_id)
        prueba = Prueba.objects.select_for_update().filter(pk=prueba_id).first()
        if prueba is None or prueba.tipo_calculo != TipoCalculo.CURVA:
            raise NoEsPruebaPorCurva()
        if existente := CurvaCalibracion.objects.filter(clave=clave).first():
            return Guardado(curva=existente, repetida=True)
        fecha = leer_fecha(datos.get("fecha_preparacion"))
        puntos = leer_puntos(datos.get("puntos"))
        ajuste = ajustar(puntos)
        anterior = prueba.curvas.select_for_update().filter(vigente=True).first()
        if anterior:
            anterior.vigente = False
            anterior.save(update_fields=["vigente"])
        curva = CurvaCalibracion.objects.create(
            prueba=prueba,
            fecha_preparacion=fecha,
            observacion=str(datos.get("observacion") or "").strip(),
            archivo_origen=str(datos.get("archivo_origen") or "").strip()[:255],
            pendiente=ajuste.pendiente,
            ordenada=ajuste.ordenada,
            r2=ajuste.r2,
            concentracion_min=ajuste.concentracion_min,
            concentracion_max=ajuste.concentracion_max,
            absorbancia_min=ajuste.absorbancia_min,
            absorbancia_max=ajuste.absorbancia_max,
            vigente=True,
            cargada_por=usuario,
            fecha_carga=timezone.now(),
            clave=clave,
        )
        PuntoCurva.objects.bulk_create(
            PuntoCurva(curva=curva, orden=n, concentracion=c, absorbancia=a)
            for n, (c, a) in enumerate(puntos, start=1)
        )
        calculadas = sum(_calcular_pendientes(estudio, prueba) for estudio in estudios)
        return Guardado(curva=curva, anterior=anterior, calculadas=calculadas)


def _calcular_pendientes(estudio, prueba):
    """Calcula con la curva nueva las mediciones de la prueba que esperaban curva en un estudio
    ya bloqueado (FR-025). Vuelve a buscarlas bajo el bloqueo; devuelve cuántas calculó."""
    from estudios import calculo
    from estudios.models import Resultado

    if not estudio.admite_mediciones:
        return 0
    asignaciones = [a for a in pendientes_de_curva(prueba=prueba) if a.estudio_id == estudio.pk]
    if not asignaciones:
        return 0
    calculo.recalcular(estudio, asignaciones)
    return Resultado.objects.filter(asignacion__in=asignaciones).count()


# --- Borrar -----------------------------------------------------------------------------------


def borrar_curva(*, usuario, curva_id):
    """Borra una curva que nunca se usó (FR-015). Si era la vigente, vuelve a quedar vigente la
    anterior más reciente (por fecha de carga). Devuelve la vigente que queda, o None.

    Bajo el lock exclusivo de la prueba: un cálculo que la está usando (lock compartido) termina
    antes y la deja `usada`, así que el borrado se rechaza en vez de chocar con la FK (R5, R6).
    """
    from .gestion import autorizar
    from .models import CurvaCalibracion

    autorizar(usuario)
    with transaction.atomic():
        prueba_id = (
            CurvaCalibracion.objects.filter(pk=curva_id).values_list("prueba_id", flat=True).first()
        )
        if prueba_id is None:
            raise CurvaError("La curva ya no existe.")
        bloquear_prueba(prueba_id)
        curva = CurvaCalibracion.objects.select_for_update().filter(pk=curva_id).first()
        if curva is None:
            raise CurvaError("La curva ya no existe.")
        if curva.usada or curva.resultados.exists():
            raise CurvaUsada()
        era_vigente = curva.vigente
        curva.delete()
        restantes = CurvaCalibracion.objects.select_for_update().filter(prueba_id=prueba_id)
        if not era_vigente:
            return restantes.filter(vigente=True).first()
        nueva = restantes.order_by("-fecha_carga", "-pk").first()
        if nueva is not None:
            nueva.vigente = True
            nueva.save(update_fields=["vigente"])
        return nueva
