import uuid

from django.core import signing
from django.utils.crypto import salted_hmac

from .catalogo import leer_configuracion
from .servicios import CrearEstudioError, normalizar_solicitud

CLAVE_SESION = "estudios_pendientes"
SALT = "estudios.creacion.v1"
TTL = 3600


def huella_sesion(request):
    if not request.session.session_key:
        request.session.create()
    return salted_hmac("estudios.sesion", request.session.session_key).hexdigest()


def cargar_token(request, token, *, recuperar=False):
    datos = signing.loads(token, salt=SALT, max_age=None if recuperar else TTL)
    if not isinstance(datos, dict) or datos.get("usuario") != request.user.pk:
        raise signing.BadSignature("Identidad inválida")
    if datos.get("sesion") != huella_sesion(request):
        raise signing.BadSignature("Sesión inválida")
    normalizados = normalizar_solicitud(datos)
    if min(normalizados[c] for c in ("muestra", "tipo", "version")) < 1:
        raise signing.BadSignature("Selección inválida")
    return {**normalizados, "clave": str(normalizados["clave"])}


def pendientes(request):
    return request.session.get(CLAVE_SESION, {})


def descartar(request, clave):
    borradores = dict(pendientes(request))
    borradores.pop(str(clave), None)
    request.session[CLAVE_SESION] = borradores


def preparar(request, muestra, tipo_id, *, clave=None, config=None):
    config = config if config is not None else leer_configuracion(tipo_id)
    clave = str(clave or uuid.uuid4())
    datos = {
        "clave": clave,
        "muestra": muestra.pk,
        "tipo": config["id"],
        "version": config["version"],
    }
    payload = {**datos, "usuario": request.user.pk, "sesion": huella_sesion(request)}
    borrador = {
        "datos": datos,
        "config": config,
        "muestra": {
            "pi": muestra.numero_pi,
            "cliente": muestra.cliente.nombre_completo,
            "origen": muestra.origen.nombre,
        },
        "token": signing.dumps(payload, salt=SALT, compress=True),
    }
    borradores = dict(pendientes(request))
    # Cota por sesión: evita crecimiento indefinido por formularios abandonados.
    if clave not in borradores and len(borradores) >= 20:
        raise CrearEstudioError(
            "Hay demasiadas solicitudes pendientes. Cancelá alguna para continuar."
        )
    borradores[clave] = borrador
    request.session[CLAVE_SESION] = borradores
    return borrador
