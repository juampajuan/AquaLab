"""Calidad del agua del período (US 8.4): sección «Calidad» del dashboard.

Única fuente de sus cálculos. Recibe el `Periodo` de `informes.tablero` (el mismo del selector) y
cuenta las validaciones vigentes fechadas en el período, en la zona del laboratorio, con la
evaluación guardada al validar: nunca reevalúa con los límites actuales. «Sin límite comparable»
queda fuera de los porcentajes. Todo en `Decimal`; el orden usa la fracción exacta. Solo lectura.
Ver specs/033-panel-calidad/.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

from django.db.models import Count, Q

from estudios.models import Validacion
from informes import tablero
from pruebas.limites import Evaluacion

MINIMO_EVALUADOS_RANKING = 5
TOPE_LISTA = 10
EVALUADAS = (Evaluacion.CUMPLE, Evaluacion.FUERA_DE_NORMA)
UN_DECIMAL = Decimal("0.1")


# --- Base ------------------------------------------------------------------------------------


def porcentaje(parte, total):
    """`parte` sobre `total` en %, con un decimal (la mitad hacia arriba); None si no hay total."""
    if not total:
        return None
    return (Decimal(parte) * 100 / Decimal(total)).quantize(UN_DECIMAL, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Conteo:
    fuera: int
    evaluados: int

    @property
    def porcentaje(self):
        return porcentaje(self.fuera, self.evaluados)

    @property
    def fraccion(self):
        """La proporción exacta fuera de norma, para ordenar sin el redondeo."""
        return Fraction(self.fuera, self.evaluados) if self.evaluados else Fraction(0)

    @property
    def porcentaje_texto(self):
        """«20,0 %»; vacío sin evaluados."""
        return "" if not self.evaluados else f"{tablero.con_coma(self.porcentaje)} %"

    @property
    def texto(self):
        """«20,0 % (2 de 10)»; «Sin resultados» sin evaluados."""
        if not self.evaluados:
            return "Sin resultados"
        return f"{self.porcentaje_texto} ({self.fuera} de {self.evaluados})"


@dataclass(frozen=True)
class Lista:
    filas: list
    restantes: int


def recortar(filas):
    return Lista(filas[:TOPE_LISTA], max(0, len(filas) - TOPE_LISTA))


def vigentes():
    """Validaciones vigentes con su día de validación en la zona del laboratorio."""
    return Validacion.objects.filter(anulada=False).annotate(
        dia=tablero.fecha_local("fecha_validacion")
    )


def en_periodo(p):
    return Q(dia__range=(p.inicio, p.fin))


def contar():
    """Anotaciones `fuera` y `evaluados` sobre la evaluación guardada."""
    return {
        "fuera": Count("pk", filter=Q(evaluacion=Evaluacion.FUERA_DE_NORMA)),
        "evaluados": Count("pk", filter=Q(evaluacion__in=EVALUADAS)),
    }


# --- Indicador general (US1) -----------------------------------------------------------------


@dataclass(frozen=True)
class VariacionCalidad:
    tono: str
    texto: str


@dataclass(frozen=True)
class IndicadorCalidad:
    actual: Conteo
    anterior: Conteo
    sin_limite: int
    variacion: VariacionCalidad | None


def variacion_calidad(actual, anterior):
    """Diferencia en puntos porcentuales («▲ +5,0 p. p.»); subir es desfavorable. None si a alguno
    de los dos períodos le faltan resultados evaluados."""
    v = tablero.variacion(actual.porcentaje, anterior.porcentaje, favorable_si_sube=False)
    if v is None:
        return None
    return VariacionCalidad(v.tono, f"{v.simbolo} {tablero.con_signo(v.diferencia)} p. p.")


def indicador(p):
    """Porcentaje fuera de norma del período y del anterior, en una consulta."""
    actual = en_periodo(p)
    anterior = Q(dia__range=(p.inicio_anterior, p.fin_anterior))
    fuera = Q(evaluacion=Evaluacion.FUERA_DE_NORMA)
    evaluados = Q(evaluacion__in=EVALUADAS)
    datos = vigentes().aggregate(
        fuera=Count("pk", filter=actual & fuera),
        evaluados=Count("pk", filter=actual & evaluados),
        fuera_anterior=Count("pk", filter=anterior & fuera),
        evaluados_anterior=Count("pk", filter=anterior & evaluados),
        sin_limite=Count("pk", filter=actual & Q(evaluacion=Evaluacion.SIN_LIMITE)),
    )
    conteo_actual = Conteo(datos["fuera"], datos["evaluados"])
    conteo_anterior = Conteo(datos["fuera_anterior"], datos["evaluados_anterior"])
    return IndicadorCalidad(
        conteo_actual,
        conteo_anterior,
        datos["sin_limite"],
        variacion_calidad(conteo_actual, conteo_anterior),
    )


# --- Pruebas que más fallan (US2) ------------------------------------------------------------


@dataclass(frozen=True)
class FilaPrueba:
    codigo: str
    nombre: str
    conteo: Conteo

    @property
    def etiqueta(self):
        return f"{self.codigo} · {self.nombre}"


def pruebas(p):
    """Pruebas con al menos `MINIMO_EVALUADOS_RANKING` evaluados y algún fuera de norma, de mayor
    a menor proporción; a igual proporción, más fuera de norma primero y después por código."""
    filas = (
        vigentes()
        .filter(en_periodo(p), evaluacion__in=EVALUADAS)
        .values("asignacion__prueba", "asignacion__prueba__codigo", "asignacion__prueba__nombre")
        .annotate(**contar())
        .filter(evaluados__gte=MINIMO_EVALUADOS_RANKING, fuera__gte=1)
        .order_by()
    )
    ranking = [
        FilaPrueba(
            fila["asignacion__prueba__codigo"],
            fila["asignacion__prueba__nombre"],
            Conteo(fila["fuera"], fila["evaluados"]),
        )
        for fila in filas
    ]
    ranking.sort(key=lambda f: (-f.conteo.fraccion, -f.conteo.fuera, f.codigo))
    return recortar(ranking)


# --- Contexto --------------------------------------------------------------------------------


def armar(p):
    """Todo el contexto de la sección «Calidad» para el período `p` (de `tablero.periodo`)."""
    ranking = pruebas(p)
    return {
        "indicador": indicador(p),
        "pruebas": ranking,
        "minimo_ranking": MINIMO_EVALUADOS_RANKING,
        # Para Chart.js (json_script): los porcentajes van como texto para no pasar por float.
        "graficos": {
            "calidad_pruebas": {
                "etiquetas": [fila.etiqueta for fila in ranking.filas],
                "porcentajes": [str(fila.conteo.porcentaje) for fila in ranking.filas],
            },
        },
    }
