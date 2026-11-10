"""Consultas de pendientes compartidas por Inicio y la búsqueda; no modifican datos."""

from django.db.models import Exists, OuterRef

from .models import (
    EstadoEstudio,
    EstadoPruebaEstudio,
    PruebaEstudio,
    Resultado,
    Validacion,
)


def asignaciones_con_mediciones_pendientes():
    return PruebaEstudio.objects.filter(
        estado=EstadoPruebaEstudio.PENDIENTE, prueba__es_calculada=False
    )


def estudios_con_mediciones_pendientes(qs):
    return qs.filter(
        estado__in=(EstadoEstudio.PENDIENTE_ANALISIS, EstadoEstudio.EN_PROCESO)
    ).filter(Exists(asignaciones_con_mediciones_pendientes().filter(estudio_id=OuterRef("pk"))))


def resultados_por_validar():
    vigentes = Validacion.objects.filter(asignacion_id=OuterRef("asignacion_id"), anulada=False)
    return (
        Resultado.objects.filter(asignacion__estado=EstadoPruebaEstudio.CARGADA)
        .exclude(asignacion__estudio__estado=EstadoEstudio.INFORME_GENERADO)
        .filter(~Exists(vigentes))
    )


def estudios_con_resultados_pendientes(qs):
    return qs.filter(Exists(resultados_por_validar().filter(asignacion__estudio_id=OuterRef("pk"))))
