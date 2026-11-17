import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from . import conclusiones
from .forms import AprobarConclusionForm, GuardarConclusionForm, RevisionConclusionForm

MENSAJES_RESPALDO = {
    "sin_configuracion": "La redacción asistida no está disponible.",
    "no_disponible": "No se pudo obtener la redacción asistida.",
    "cuota": "La redacción asistida no está disponible en este momento.",
    "respuesta_invalida": "No se pudo utilizar la redacción recibida.",
    "plazo": "Se agotó el tiempo de espera de la redacción asistida.",
    "capacidad": "La redacción asistida está ocupada en este momento.",
    "tamano": "No se pudo procesar la redacción asistida para estos datos.",
}


def presentar_estado(estado):
    """Solo códigos conocidos se traducen a avisos; nunca errores del proveedor."""
    aviso = ""
    if estado.get("origen_propuesta") == "plantilla":
        motivo = MENSAJES_RESPALDO.get(estado.get("motivo_respaldo"), "")
        parcial = estado.get("hechos", {}).get("clase") == "parcial"
        plantilla = "una plantilla de respaldo parcial" if parcial else "una plantilla de respaldo"
        aviso = f"{motivo} Se conserva {plantilla}. Revisala y aprobala expresamente.".strip()
    return {**estado, "aviso_respaldo": aviso}


@never_cache
@require_POST
def proponer(request, pk):
    return ejecutar(request, pk, RevisionConclusionForm, conclusiones.proponer_conclusion)


@never_cache
@require_POST
def guardar(request, pk):
    return ejecutar(request, pk, GuardarConclusionForm, conclusiones.guardar_borrador)


@never_cache
@require_POST
def aprobar(request, pk):
    return ejecutar(request, pk, AprobarConclusionForm, conclusiones.aprobar_conclusion)


def ejecutar(request, pk, formulario, servicio):
    try:
        conclusiones.autorizar_conclusion(request.user)
    except PermissionDenied:
        return JsonResponse({"error": "Se requiere un bioquímico autorizado."}, status=403)
    try:
        datos = json.loads(request.body)
        if not isinstance(datos, dict):
            raise ValueError
        if type(datos.get("revision_esperada")) is not int:
            raise ValueError
        for nombre in ("huella_hechos_vista", "huella_texto_visto", "texto"):
            if nombre in formulario.base_fields and not isinstance(datos.get(nombre), str):
                raise ValueError
        if "confirmacion" in formulario.base_fields and type(datos.get("confirmacion")) is not bool:
            raise ValueError
    except (ValueError, UnicodeDecodeError):
        return JsonResponse(
            {"error": "Los datos del borrador no tienen el formato esperado."}, status=400
        )
    try:
        entrada = conclusiones.validar_entrada(formulario, datos)
        estado = servicio(pk, request.user, **entrada)
    except ValidationError as exc:
        errores = exc.message_dict if hasattr(exc, "message_dict") else {"__all__": exc.messages}
        return JsonResponse(
            {"error": "Revisá los campos indicados.", "errores": errores}, status=400
        )
    except conclusiones.ConflictoConclusion as exc:
        return JsonResponse({**presentar_estado(exc.estado), "error": str(exc)}, status=409)
    except PermissionDenied:
        return JsonResponse({"error": "Ya no tenés autorización para esta acción."}, status=403)
    except Http404:
        return JsonResponse({"error": "El estudio no está disponible."}, status=404)
    return JsonResponse(presentar_estado(estado))
