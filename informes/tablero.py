"""Cálculos del dashboard del laboratorio (US 8.3).

Única fuente de los indicadores: períodos y su período anterior, conteos, tiempo de respuesta,
series de los gráficos y alertas. Todo se cuenta en la zona horaria del laboratorio y las funciones
reciben `hoy` o `ahora` para poder probarlas con fechas fijas. Solo lectura. Ver
specs/027-panel-laboratorio/.
"""

import calendar
import datetime as dt
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Avg, Count, DateField, F, Max, OuterRef, Q, Subquery
from django.db.models.functions import Cast, Greatest, TruncDate, TruncMonth, TruncWeek
from django.utils import timezone

from estudios.models import EstadoEstudio, Estudio, Medicion, Validacion
from informes.models import Informe
from muestras.models import Muestra

PERIODOS = {
    "este_mes": "Este mes",
    "mes_anterior": "Mes anterior",
    "ultimos_3": "Últimos 3 meses",
    "ultimos_6": "Últimos 6 meses",
}
DIAS_SIN_AVANZAR = 7
MESES_GRAFICO = 6
SEMANAS_GRAFICO = 12
MESES_ABREVIADOS = (
    "ene",
    "feb",
    "mar",
    "abr",
    "may",
    "jun",
    "jul",
    "ago",
    "sep",
    "oct",
    "nov",
    "dic",
)
UN_DECIMAL = Decimal("0.1")


# --- Períodos --------------------------------------------------------------------------------


@dataclass(frozen=True)
class Periodo:
    clave: str
    etiqueta: str
    inicio: dt.date
    fin: dt.date
    inicio_anterior: dt.date
    fin_anterior: dt.date


def correr_meses(fecha, meses):
    """La misma fecha `meses` meses antes (negativo) o después, con el día recortado al último del
    mes de destino."""
    total = fecha.year * 12 + fecha.month - 1 + meses
    anio, mes = total // 12, total % 12 + 1
    return dt.date(anio, mes, min(fecha.day, calendar.monthrange(anio, mes)[1]))


def ultimo_dia(fecha):
    return fecha.replace(day=calendar.monthrange(fecha.year, fecha.month)[1])


def periodo(clave, hoy):
    """El período elegido y su período anterior, como fechas locales inclusivas (research R2).
    Una clave desconocida vale «Este mes»."""
    if clave not in PERIODOS:
        clave = "este_mes"
    primero = hoy.replace(day=1)
    if clave == "mes_anterior":
        inicio = correr_meses(primero, -1)
        fin = ultimo_dia(inicio)
        inicio_anterior = correr_meses(inicio, -1)
        fin_anterior = ultimo_dia(inicio_anterior)
    else:
        meses = {"este_mes": 1, "ultimos_3": 3, "ultimos_6": 6}[clave]
        inicio = correr_meses(primero, -(meses - 1))
        fin = hoy
        inicio_anterior = correr_meses(inicio, -meses)
        fin_anterior = correr_meses(fin, -meses)
    return Periodo(clave, PERIODOS[clave], inicio, fin, inicio_anterior, fin_anterior)


# --- Variación -------------------------------------------------------------------------------


@dataclass(frozen=True)
class Variacion:
    diferencia: object
    porcentaje: int | None
    sentido: str
    simbolo: str
    tono: str

    @property
    def texto(self):
        """«▲ +5 (+12 %)», «▼ −2 (−8 %)», «= 0 (0 %)» o «▲ +3 (sin datos previos)»."""
        relativo = (
            "sin datos previos" if self.porcentaje is None else f"{con_signo(self.porcentaje)} %"
        )
        return f"{self.simbolo} {con_signo(self.diferencia)} ({relativo})"


def con_signo(numero):
    if numero > 0:
        return "+" + str(numero).replace(".", ",")
    if numero < 0:
        return "−" + str(-numero).replace(".", ",")
    return str(numero).replace(".", ",")


def variacion(actual, anterior, *, favorable_si_sube=True):
    """Diferencia, porcentaje (None si el anterior es 0), sentido y tono según si el cambio es
    favorable (research R4). Sin alguno de los dos valores no hay variación."""
    if actual is None or anterior is None:
        return None
    diferencia = actual - anterior
    porcentaje = None
    if anterior:
        porcentaje = int(
            (Decimal(diferencia) * 100 / Decimal(anterior)).quantize(
                Decimal(1), rounding=ROUND_HALF_UP
            )
        )
    if diferencia > 0:
        sentido, simbolo = "sube", "▲"
    elif diferencia < 0:
        sentido, simbolo = "baja", "▼"
    else:
        sentido, simbolo = "igual", "="
    if sentido == "igual":
        tono = "neutro"
    else:
        tono = "exito" if (sentido == "sube") == favorable_si_sube else "peligro"
    return Variacion(diferencia, porcentaje, sentido, simbolo, tono)


# --- Indicadores -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Indicador:
    actual: object
    anterior: object
    variacion: Variacion | None

    @property
    def texto(self):
        return "—" if self.actual is None else con_coma(self.actual)


def fecha_local(campo):
    return TruncDate(campo, tzinfo=timezone.get_current_timezone())


def _contar(queryset, campo_fecha, p):
    conteo = queryset.annotate(dia=campo_fecha).aggregate(
        actual=Count("pk", filter=Q(dia__range=(p.inicio, p.fin))),
        anterior=Count("pk", filter=Q(dia__range=(p.inicio_anterior, p.fin_anterior))),
    )
    return Indicador(
        conteo["actual"], conteo["anterior"], variacion(conteo["actual"], conteo["anterior"])
    )


def tiempo_respuesta(desde, hasta):
    """Promedio de días corridos entre el ingreso de la muestra y la emisión de los informes
    emitidos entre `desde` y `hasta` (fechas locales), con un decimal; None sin informes."""
    promedio = (
        Informe.objects.annotate(dia=fecha_local("fecha_emision"))
        .filter(dia__range=(desde, hasta))
        .annotate(dias=F("dia") - F("estudio__muestra__fecha_ingreso"))
        .aggregate(promedio=Avg("dias"))["promedio"]
    )
    return redondear(promedio)


def redondear(valor):
    """Días promedio con un decimal. La resta de fechas llega como `timedelta` (o como número,
    según el motor); se convierte sin pasar por `float`."""
    if valor is None:
        return None
    if isinstance(valor, dt.timedelta):
        dias = (
            Decimal(valor.days)
            + Decimal(valor.seconds) / 86400
            + Decimal(valor.microseconds) / 86_400_000_000
        )
    else:
        dias = Decimal(str(valor))
    return dias.quantize(UN_DECIMAL, rounding=ROUND_HALF_UP)


def con_coma(valor):
    """Número para mostrar con coma decimal (7.5 → «7,5»)."""
    return str(valor).replace(".", ",")


def indicadores(p):
    """Muestras, estudios e informes del período con su variación, y el tiempo de respuesta."""
    actual = tiempo_respuesta(p.inicio, p.fin)
    anterior = tiempo_respuesta(p.inicio_anterior, p.fin_anterior)
    return {
        "muestras": _contar(Muestra.objects.all(), F("fecha_ingreso"), p),
        "estudios": _contar(Estudio.objects.all(), fecha_local("fecha_creacion"), p),
        "informes": _contar(Informe.objects.all(), fecha_local("fecha_emision"), p),
        "respuesta": Indicador(
            actual, anterior, variacion(actual, anterior, favorable_si_sube=False)
        ),
    }


def estudios_por_estado():
    """`(etiqueta, cantidad, valor)` de cada estado hoy, en el orden del ciclo del estudio."""
    conteo = dict(Estudio.objects.values_list("estado").annotate(total=Count("pk")).order_by())
    return [(etiqueta, conteo.get(valor, 0), valor) for valor, etiqueta in EstadoEstudio.choices]


# --- Series de los gráficos --------------------------------------------------------------------


def serie_mensual(hoy):
    """Tiempo de respuesta promedio de cada uno de los últimos 6 meses (incluido el actual)."""
    primero = correr_meses(hoy.replace(day=1), -(MESES_GRAFICO - 1))
    zona = timezone.get_current_timezone()
    promedios = {
        fila["mes"].date() if hasattr(fila["mes"], "date") else fila["mes"]: fila["promedio"]
        for fila in Informe.objects.annotate(dia=fecha_local("fecha_emision"))
        .filter(dia__range=(primero, hoy))
        .annotate(
            mes=TruncMonth("fecha_emision", tzinfo=zona),
            dias=F("dia") - F("estudio__muestra__fecha_ingreso"),
        )
        .values("mes")
        .annotate(promedio=Avg("dias"))
        .order_by()
    }
    serie = []
    for i in range(MESES_GRAFICO):
        mes = correr_meses(primero, i)
        dias = redondear(promedios.get(mes))
        serie.append(
            {
                "mes": mes,
                "etiqueta": f"{MESES_ABREVIADOS[mes.month - 1]} {mes.year}",
                "dias": dias,
                "texto": "—" if dias is None else con_coma(dias),
            }
        )
    return serie


def serie_semanal(hoy):
    """Muestras ingresadas e informes emitidos en cada una de las últimas 12 semanas (lunes a
    domingo, incluida la actual)."""
    lunes = hoy - dt.timedelta(days=hoy.weekday())
    desde = lunes - dt.timedelta(weeks=SEMANAS_GRAFICO - 1)
    hasta = lunes + dt.timedelta(days=6)
    muestras = dict(
        Muestra.objects.filter(fecha_ingreso__range=(desde, hasta))
        .annotate(semana=Cast(TruncWeek("fecha_ingreso"), DateField()))
        .values_list("semana")
        .annotate(total=Count("pk"))
        .order_by()
    )
    informes = dict(
        Informe.objects.annotate(dia=fecha_local("fecha_emision"))
        .filter(dia__range=(desde, hasta))
        .annotate(semana=Cast(TruncWeek("dia"), DateField()))
        .values_list("semana")
        .annotate(total=Count("pk"))
        .order_by()
    )
    serie = []
    for i in range(SEMANAS_GRAFICO):
        semana = desde + dt.timedelta(weeks=i)
        serie.append(
            {
                "desde": semana,
                "etiqueta": semana.strftime("%d/%m"),
                "muestras": muestras.get(semana, 0),
                "informes": informes.get(semana, 0),
            }
        )
    return serie


# --- Alertas ---------------------------------------------------------------------------------


def _maximo(modelo, campo, filtro):
    return Subquery(
        modelo.objects.filter(**{filtro: OuterRef("pk")})
        .order_by()
        .values(filtro)
        .annotate(maximo=Max(campo))
        .values("maximo")[:1]
    )


def dias_desde(momento, ahora):
    return (timezone.localdate(ahora) - timezone.localtime(momento).date()).days


def alertas(ahora):
    """Estudios sin avanzar hace más de 7 días y Finalizados sin informe (research R7), del más
    antiguo al más reciente."""
    ultima = Greatest(
        "fecha_creacion",
        _maximo(Medicion, "fecha_carga", "asignacion__estudio"),
        _maximo(Medicion, "fecha_correccion", "asignacion__estudio"),
        _maximo(Validacion, "fecha_validacion", "asignacion__estudio"),
    )
    sin_avanzar = (
        Estudio.objects.filter(
            estado__in=(EstadoEstudio.PENDIENTE_ANALISIS, EstadoEstudio.EN_PROCESO)
        )
        .annotate(ultima_actividad=ultima)
        .filter(ultima_actividad__lt=ahora - dt.timedelta(days=DIAS_SIN_AVANZAR))
        .select_related("muestra__cliente")
        .order_by("ultima_actividad", "pk")
    )
    finalizados = (
        Estudio.objects.filter(estado=EstadoEstudio.FINALIZADO, informe__isnull=True)
        .annotate(
            finalizado_en=Subquery(
                Validacion.objects.filter(asignacion__estudio=OuterRef("pk"), anulada=False)
                .order_by("-fecha_validacion")
                .values("fecha_validacion")[:1]
            )
        )
        .select_related("muestra__cliente")
        .order_by(F("finalizado_en").asc(nulls_first=True), "pk")
    )
    return {
        "sin_avanzar": [
            {"estudio": e, "dias": dias_desde(e.ultima_actividad, ahora)} for e in sin_avanzar
        ],
        "finalizados_sin_informe": [
            {
                "estudio": e,
                "dias": dias_desde(e.finalizado_en, ahora) if e.finalizado_en else None,
            }
            for e in finalizados
        ],
    }


TARJETAS = (
    ("muestras", "Muestras ingresadas", "flask-conical"),
    ("estudios", "Estudios creados", "microscope"),
    ("informes", "Informes emitidos", "file-text"),
    ("respuesta", "Tiempo de respuesta", "clock"),
)


def armar(clave, ahora=None):
    """Todo el contexto del dashboard para el período `clave`."""
    ahora = ahora or timezone.now()
    hoy = timezone.localdate(ahora)
    p = periodo(clave, hoy)
    datos = indicadores(p)
    mensual = serie_mensual(hoy)
    semanal = serie_semanal(hoy)
    return {
        "periodo": p,
        "periodos": PERIODOS,
        "tarjetas": [
            {"nombre": nombre, "titulo": titulo, "icono": icono, "indicador": datos[nombre]}
            for nombre, titulo, icono in TARJETAS
        ],
        "estados": estudios_por_estado(),
        "serie_mensual": mensual,
        "serie_semanal": semanal,
        "alertas": alertas(ahora),
        # Para Chart.js (json_script): los días van como texto para no pasar por float.
        "datos_graficos": {
            "respuesta": {
                "etiquetas": [m["etiqueta"] for m in mensual],
                "dias": [None if m["dias"] is None else str(m["dias"]) for m in mensual],
            },
            "actividad": {
                "etiquetas": [s["etiqueta"] for s in semanal],
                "muestras": [s["muestras"] for s in semanal],
                "informes": [s["informes"] for s in semanal],
            },
        },
    }
