from django.db import connection, transaction
from django.db.models import Count, F, Max, Q

from estudios.busqueda import filtro_busqueda
from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Estudio

from .contenido import armar_contenido
from .models import Informe


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


def estudio_listo_bloqueado(estudio_pk):
    """Bloquea el estudio y revalida la regla; lo devuelve o lanza InformeNoDisponible.

    El llamador debe estar dentro de una transacción (la emisión de la US 7.2 lo usa así).
    """
    estudio = (
        Estudio.objects.select_for_update(of=("self",))
        .select_related("muestra", "muestra__cliente", "muestra__origen")
        .filter(pk=estudio_pk)
        .first()
    )
    if estudio is None:
        raise InformeNoDisponible("El estudio no está disponible.")
    motivo = motivo_para_no_informar(estudio, list(estudio.pruebas_asignadas.all()))
    if motivo:
        raise InformeNoDisponible(motivo)
    return estudio


def comprobar_generacion(estudio_pk):
    """Revalida la regla con el estudio bloqueado y lo devuelve; si no, InformeNoDisponible."""
    with transaction.atomic():
        return estudio_listo_bloqueado(estudio_pk)


class EmitirInformeError(Exception):
    pass


# Clave fija del advisory lock que serializa la numeración de los informes (US 7.2).
CLAVE_LOCK_NUMERO_INFORME = 7_200_001


def siguiente_numero():
    ultimo = Informe.objects.aggregate(maximo=Max("numero"))["maximo"]
    return (ultimo or 0) + 1


def emitir_informe(estudio_pk, usuario):
    """Emite el informe del estudio (US 7.2) y lo devuelve.

    En una transacción: bloquea el estudio y revalida la regla de la US 7.1, toma el lock de la
    numeración (máximo + 1, sin huecos como el N° PI), guarda la copia de `armar_contenido` y pasa
    el estudio a «Informe generado». Una segunda emisión del mismo estudio espera el bloqueo y
    recibe el motivo «ya fue generado».
    """
    if not usuario.is_authenticated or not usuario.is_active:
        raise EmitirInformeError("Se requiere una sesión activa.")
    if not usuario.has_perm("informes.emitir_informes"):
        raise EmitirInformeError("Se requiere permiso para emitir informes.")
    with transaction.atomic():
        estudio = estudio_listo_bloqueado(estudio_pk)
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [CLAVE_LOCK_NUMERO_INFORME])
        informe = Informe.objects.create(
            numero=siguiente_numero(),
            estudio=estudio,
            emitido_por=usuario,
            contenido=armar_contenido(estudio),
        )
        estudio.estado = EstadoEstudio.INFORME_GENERADO
        estudio.save(update_fields=["estado"])
    return informe


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
