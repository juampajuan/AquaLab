"""Asistente de consultas (US 10.1, contracts/preguntar.md). Solo lectura: no escribe en la base
ni en la sesión. Ninguna excepción sale de la vista: la página queda igual."""

import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from . import configuracion, conversacion
from .cliente_ia import CuotaAgotada, ServicioNoDisponible
from .forms import MENSAJE_INVALIDA, PreguntaForm

logger = logging.getLogger("asistente")

MENSAJE_NO_DISPONIBLE = (
    "El asistente no está disponible en este momento. Probá de nuevo más tarde o usá las "
    "pantallas de AquaLab."
)
MENSAJE_NO_CONFIGURADO = "El asistente no está configurado."
MENSAJE_CUOTA = (
    "Se alcanzó el límite de consultas del asistente. Probá más tarde; el resto de AquaLab "
    "funciona normalmente."
)


def error(codigo, mensaje, status):
    return JsonResponse({"error": codigo, "mensaje": mensaje}, status=status)


@require_POST
def preguntar(request):
    config = configuracion.actual()
    if not config.habilitado:
        return error("no_configurado", MENSAJE_NO_CONFIGURADO, 503)
    try:
        datos = json.loads(request.body or b"")
    except ValueError:
        datos = None
    form = PreguntaForm(datos)
    if not form.is_valid():
        return error("pregunta_invalida", MENSAJE_INVALIDA, 400)
    try:
        respuesta = conversacion.responder(
            request.user,
            form.cleaned_data["pregunta"],
            form.cleaned_data["historial"],
            config=config,
        )
    except CuotaAgotada:
        return error("cuota", MENSAJE_CUOTA, 429)
    except ServicioNoDisponible:
        # Incluye el presupuesto de 20 s agotado; el tope de vueltas sale como 200 (research R9).
        return error("no_disponible", MENSAJE_NO_DISPONIBLE, 503)
    except Exception:
        logger.error("Asistente: error inesperado al responder.", exc_info=True)
        return error("no_disponible", MENSAJE_NO_DISPONIBLE, 503)
    return JsonResponse({"texto": respuesta.texto, "enlaces": respuesta.enlaces})
