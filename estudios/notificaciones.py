"""Aviso por correo de los desvíos recién calculados (US 8.2).

`calculo.recalcular` llama a `avisar_desvios` con las pruebas cuyo resultado es nuevo o cambió de
valor (un recálculo con el mismo valor no reenvía). La evaluación es la de `desvios`; el envío se
agenda con `transaction.on_commit`, así ninguna operación que se deshace avisa, y una falla de
envío solo queda en el log `estudios.notificaciones`: la carga o la corrección no se afectan.
"""

import logging
from functools import partial

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.urls import reverse

from config.correos import armar_correo, asunto_de

from . import desvios
from .models import EstadoPruebaEstudio

logger = logging.getLogger("estudios.notificaciones")

GRUPO_DESTINATARIOS = "Bioquímicos"


def avisar_desvios(estudio, codigos):
    """Agenda los correos de cada desvío entre las pruebas `codigos` del estudio. El llamador tiene
    el estudio bloqueado dentro de su transacción. No escribe nada."""
    asignaciones = list(
        estudio.pruebas_asignadas.select_related("prueba", "resultado").filter(
            prueba__codigo__in=codigos, estado=EstadoPruebaEstudio.CARGADA
        )
    )
    if not asignaciones:
        return
    regla = desvios.regla()
    evaluacion = desvios.evaluar_estudio(estudio, asignaciones, regla)
    avisos = [
        datos_del_aviso(estudio, asignacion, deteccion, regla)
        for asignacion in asignaciones
        if isinstance(deteccion := evaluacion.get(asignacion.pk), desvios.Deteccion)
    ]
    if avisos:
        transaction.on_commit(partial(enviar, avisos))


def datos_del_aviso(estudio, asignacion, deteccion, regla):
    """Los textos del correo, armados dentro de la transacción (no consulta después)."""
    muestra = estudio.muestra
    base = settings.AQUALAB_URL_BASE.rstrip("/")
    return {
        "numero_pi": muestra.numero_pi,
        "cliente": muestra.cliente.nombre_completo,
        "origen": muestra.origen.nombre,
        "prueba": f"{asignacion.prueba.nombre} ({asignacion.prueba.codigo})",
        "observado": deteccion.observado,
        "etiqueta_referencia": deteccion.etiqueta_referencia,
        "referencia": deteccion.referencia_texto,
        "variacion": deteccion.variacion_texto,
        "regla": desvios.texto_regla(regla),
        "enlace": base + reverse("estudios:detalle", args=[estudio.pk]),
    }


def enviar(avisos):
    """Un correo por aviso y por bioquímico activo, cada uno con un solo destinatario en «Para»
    (nadie ve las direcciones de los otros). Nunca relanza una falla."""
    destinatarios = list(
        get_user_model()
        .objects.filter(is_active=True, groups__name=GRUPO_DESTINATARIOS)
        .order_by("email")
        .values_list("email", flat=True)
        .distinct()
    )
    if not destinatarios:
        logger.warning("Desvío sin bioquímicos activos para avisar (%d avisos)", len(avisos))
        return
    for aviso in avisos:
        asunto = asunto_de("estudios/correos/desvio_asunto.txt", aviso)
        for destinatario in destinatarios:
            try:
                armar_correo(
                    asunto,
                    "estudios/correos/desvio_cuerpo.txt",
                    "estudios/correos/desvio_cuerpo.html",
                    aviso,
                    to=[destinatario],
                ).send()
            except Exception:
                logger.exception(
                    "No se pudo enviar el aviso de desvío de %s (N° PI %s) a %s",
                    aviso["prueba"],
                    aviso["numero_pi"],
                    destinatario,
                )
