from django.db import transaction
from django.db.models import Count, F, Q

from estudios.busqueda import filtro_busqueda
from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Estudio


class InformeNoDisponible(Exception):
    """El estudio no se puede informar; el mensaje es el motivo."""


def motivo_para_no_informar(estudio, asignaciones):
    """Motivo por el que no se puede generar el informe del estudio, o None si se puede (US 7.1).

    Es la única regla para informar: la usan el control, `comprobar_generacion` y, en SQL,
    `estudios_para_informar(solo_listos=True)`.
    """
    if estudio.estado == EstadoEstudio.INFORME_GENERADO:
        return "El informe de este estudio ya fue generado."
    if not asignaciones:
        return "El estudio no tiene pruebas."
    faltan = sum(1 for a in asignaciones if a.estado != EstadoPruebaEstudio.COMPLETADA)
    if faltan == 1:
        return "Hay 1 prueba sin completar."
    if faltan:
        return f"Hay {faltan} pruebas sin completar."
    return None


def comprobar_generacion(estudio_pk):
    """Revalida la regla con el estudio bloqueado y lo devuelve; si no, InformeNoDisponible.

    US 7.2 debe crear el informe dentro de esta misma transacción, con el estudio bloqueado como
    en `cargar_mediciones` y `corregir_mediciones`.
    """
    with transaction.atomic():
        estudio = Estudio.objects.select_for_update().get(pk=estudio_pk)
        motivo = motivo_para_no_informar(estudio, list(estudio.pruebas_asignadas.all()))
        if motivo:
            raise InformeNoDisponible(motivo)
        return estudio


def estudios_para_informar(q, solo_listos):
    """Estudios de la búsqueda, anotados con total_pruebas y pruebas_completadas."""
    qs = (
        Estudio.objects.select_related("muestra", "muestra__cliente", "muestra__origen")
        .annotate(
            total_pruebas=Count("pruebas_asignadas", distinct=True),
            pruebas_completadas=Count(
                "pruebas_asignadas",
                filter=Q(pruebas_asignadas__estado=EstadoPruebaEstudio.COMPLETADA),
                distinct=True,
            ),
        )
        .order_by(*Estudio._meta.ordering)
    )
    if q:
        qs = qs.filter(filtro_busqueda(q))
    if solo_listos:
        # Las mismas tres condiciones que motivo_para_no_informar.
        qs = qs.filter(total_pruebas__gt=0, pruebas_completadas=F("total_pruebas")).exclude(
            estado=EstadoEstudio.INFORME_GENERADO
        )
    return qs
