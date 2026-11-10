"""Borradores firmados de la gestión del catálogo (SCRUM-73).

Mismo esquema que `estudios/confirmaciones_tipos.py` (US 5.5): el formulario guarda en la sesión
un borrador con la operación, la prueba, la versión vista y los datos; la confirmación lleva un
token firmado, atado al usuario y a la sesión, que tiene que coincidir con ese borrador.
"""

import hashlib
import json
import time
import uuid

from django.core import signing
from django.utils.crypto import salted_hmac

CLAVE_SESION = "pruebas_pendientes"
SALT_CONTEXTO = "pruebas.contexto.v1"
SALT_CONFIRMACION = "pruebas.confirmacion.v1"
TTL = 3600
MAX_PENDIENTES = 20


def huella(request):
    if not request.session.session_key:
        request.session.create()
    return salted_hmac("pruebas.sesion.v1", request.session.session_key).hexdigest()


def identidad(request):
    return {"usuario": request.user.pk, "sesion": huella(request)}


def cargar(request, token, salt):
    datos = signing.loads(token, salt=salt, max_age=TTL)
    if not isinstance(datos, dict) or any(datos.get(k) != v for k, v in identidad(request).items()):
        raise signing.BadSignature("Identidad inválida.")
    return datos


def crear_contexto(request, operacion, prueba_id=None, version=None):
    return signing.dumps(
        {**identidad(request), "operacion": operacion, "prueba_id": prueba_id, "version": version},
        salt=SALT_CONTEXTO,
    )


def leer_contexto(request, token, operacion, prueba_id=None):
    contexto = cargar(request, token, SALT_CONTEXTO)
    if contexto.get("operacion") != operacion or contexto.get("prueba_id") != prueba_id:
        raise signing.BadSignature("Contexto inválido.")
    return contexto


def digest(datos):
    return hashlib.sha256(
        json.dumps(datos, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def pendientes(request):
    ahora = time.time()
    vigentes = {
        k: v
        for k, v in request.session.get(CLAVE_SESION, {}).items()
        if 0 <= ahora - v.get("creado_en", 0) <= TTL
    }
    request.session[CLAVE_SESION] = vigentes
    return vigentes


def descartar(request, clave):
    copia = dict(pendientes(request))
    copia.pop(str(clave), None)
    request.session[CLAVE_SESION] = copia


def preparar(request, operacion, prueba_id, version, datos, *, anterior=None):
    borradores = dict(pendientes(request))
    if anterior:
        borradores.pop(str(anterior), None)
    if len(borradores) >= MAX_PENDIENTES:
        raise signing.BadSignature("Hay demasiadas solicitudes pendientes. Cancelá alguna.")
    clave = str(uuid.uuid4())
    datos = json.loads(json.dumps(datos))
    payload = {
        **identidad(request),
        "clave": clave,
        "operacion": operacion,
        "prueba_id": prueba_id,
        "version": version,
        "digest": digest(datos),
    }
    borrador = {
        "clave": clave,
        "operacion": operacion,
        "prueba_id": prueba_id,
        "version": version,
        "datos": datos,
        "creado_en": time.time(),
        "token": signing.dumps(payload, salt=SALT_CONFIRMACION),
    }
    borradores[clave] = borrador
    request.session[CLAVE_SESION] = borradores
    return borrador


def verificar(request, token):
    payload = cargar(request, token, SALT_CONFIRMACION)
    borrador = pendientes(request).get(payload.get("clave"))
    if not borrador:
        raise signing.BadSignature("La solicitud ya no está pendiente.")
    for campo in ("clave", "operacion", "prueba_id", "version"):
        if payload.get(campo) != borrador.get(campo):
            raise signing.BadSignature("La solicitud no coincide.")
    if payload.get("digest") != digest(borrador["datos"]):
        raise signing.BadSignature("La propuesta cambió.")
    return borrador
