"""Firmas de ficha y borradores propios del panel; nunca sustituyen autorización."""

import hashlib
import json
import time
import uuid

from django.core import signing
from django.utils.crypto import salted_hmac

TTL = 3600
MAX_PENDIENTES = 20
CLAVE_SESION = "administracion_pendientes"
SALT_FICHA = "usuarios.ficha.v1"
SALT_CONFIRMACION = "usuarios.confirmacion.v1"


def identidad(request):
    if not request.session.session_key:
        request.session.create()
    return {
        "actor": request.user.pk,
        "sesion": salted_hmac("usuarios.sesion.v1", request.session.session_key).hexdigest(),
    }


def cargar(request, token, salt):
    datos = signing.loads(token, salt=salt, max_age=TTL)
    if not isinstance(datos, dict) or any(datos.get(k) != v for k, v in identidad(request).items()):
        raise signing.BadSignature("Identidad inválida.")
    return datos


def firmar_ficha(request, original, *, operacion="editar"):
    return signing.dumps(
        {**identidad(request), "operacion": operacion, "original": original}, salt=SALT_FICHA
    )


def leer_ficha(request, token, *, operacion="editar"):
    datos = cargar(request, token, SALT_FICHA)
    if datos.get("operacion") != operacion:
        raise signing.BadSignature("Operación inválida.")
    return datos["original"]


def digest(datos):
    return hashlib.sha256(
        json.dumps(datos, sort_keys=True, separators=(",", ":")).encode()
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


def preparar(request, operacion, usuario_id, version, datos, original):
    from .permisos_administracion import autorizar_administracion
    from .servicios_administracion import (
        GestionUsuarioError,
        bloquear,
        comprobar_revision,
        instantanea,
    )

    autorizar_administracion(request.user)
    if operacion not in {"aprobar", "rechazar", "estado", "rol"}:
        raise signing.BadSignature("Operación inválida.")
    esperados = {"estado": "activa", "rol": "bioquimico"}
    campo = esperados.get(operacion)
    if (campo and (set(datos) != {campo} or type(datos[campo]) is not bool)) or (
        not campo and datos
    ):
        raise signing.BadSignature("Propuesta inválida.")
    with bloquear(request, [usuario_id]) as filas:
        vigente = filas.get(usuario_id)
        if vigente is None:
            raise GestionUsuarioError("La cuenta ya no está disponible.")
        comprobar_revision(vigente, version, original)
        original = instantanea(vigente)
    borradores = dict(pendientes(request))
    if len(borradores) >= MAX_PENDIENTES:
        raise signing.BadSignature("Hay demasiadas solicitudes pendientes. Cancelá alguna.")
    clave = str(uuid.uuid4())
    propuesta = {
        "operacion": operacion,
        "usuario_id": usuario_id,
        "version": version,
        "datos": json.loads(json.dumps(datos)),
        "original": original,
    }
    token = signing.dumps(
        {**identidad(request), "clave": clave, "digest": digest(propuesta)}, salt=SALT_CONFIRMACION
    )
    borrador = {**propuesta, "clave": clave, "token": token, "creado_en": time.time()}
    borradores[clave] = borrador
    request.session[CLAVE_SESION] = borradores
    return borrador


def verificar(request, token):
    from .permisos_administracion import autorizar_administracion

    autorizar_administracion(request.user)
    payload = cargar(request, token, SALT_CONFIRMACION)
    borrador = pendientes(request).get(payload.get("clave"))
    if not borrador:
        raise signing.BadSignature("La solicitud ya no está pendiente.")
    propuesta = {
        k: borrador[k] for k in ("operacion", "usuario_id", "version", "datos", "original")
    }
    if payload.get("digest") != digest(propuesta):
        raise signing.BadSignature("La propuesta cambió.")
    return borrador


def descartar(request, clave):
    borradores = dict(pendientes(request))
    borradores.pop(str(clave), None)
    request.session[CLAVE_SESION] = borradores


def confirmar(request, token, *, cancelar=False):
    from .servicios_administracion import cambiar_estado_panel, cambiar_rol_panel, resolver_panel

    borrador = verificar(request, token)
    if cancelar:
        descartar(request, borrador["clave"])
        return False
    operacion = borrador["operacion"]
    argumentos = (request, borrador["usuario_id"])
    opciones = {"version": borrador["version"], "original": borrador["original"]}
    if operacion in {"aprobar", "rechazar"}:
        resultado = resolver_panel(*argumentos, operacion, **opciones)
    elif operacion == "estado":
        resultado = cambiar_estado_panel(*argumentos, borrador["datos"].get("activa"), **opciones)
    else:
        resultado = cambiar_rol_panel(*argumentos, borrador["datos"].get("bioquimico"), **opciones)
    descartar(request, borrador["clave"])
    return resultado
