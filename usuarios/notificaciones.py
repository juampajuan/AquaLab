"""Avisos por correo del alta de cuentas (US 1.3).

Los llamadores agendan estas funciones con `transaction.on_commit(...)`, así ningún correo sale
por una operación que después se revierte. Una falla de envío nunca se propaga: queda en el log
y la operación sigue igual.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from .models import Usuario

logger = logging.getLogger("usuarios.notificaciones")


def _enviar(tipo, destinatario, plantilla, contexto):
    """Envía un aviso a un único destinatario. Ante una falla, la registra y no la relanza."""
    try:
        asunto = " ".join(
            render_to_string(f"usuarios/correos/{plantilla}_asunto.txt", contexto).split()
        )
        cuerpo = render_to_string(f"usuarios/correos/{plantilla}_cuerpo.txt", contexto)
        send_mail(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [destinatario], fail_silently=False)
    except Exception:
        logger.exception("No se pudo enviar el aviso %s a %s", tipo, destinatario)


def avisar_solicitud_nueva(request, usuario):
    """Avisa a cada administrador activo que hay una solicitud de cuenta pendiente."""
    administradores = Usuario.objects.filter(is_superuser=True, is_active=True)
    if not administradores.exists():
        logger.warning("Solicitud de alta sin administradores activos para avisar")
        return
    enlace_ficha = request.build_absolute_uri(
        reverse("admin:usuarios_usuario_change", args=[usuario.pk])
    )
    for administrador in administradores:
        _enviar(
            "solicitud_nueva",
            administrador.email,
            "solicitud_nueva",
            {"administrador": administrador, "usuario": usuario, "enlace_ficha": enlace_ficha},
        )


def avisar_solicitud_recibida(request, usuario):
    """Confirma al solicitante que su solicitud quedó pendiente de aprobación."""
    _enviar("solicitud_recibida", usuario.email, "solicitud_recibida", {"usuario": usuario})


def avisar_aprobacion(request, usuario):
    """Avisa al solicitante que su cuenta fue aprobada y ya puede iniciar sesión."""
    enlace_login = request.build_absolute_uri(reverse("usuarios:login"))
    _enviar(
        "aprobacion",
        usuario.email,
        "aprobacion",
        {"usuario": usuario, "enlace_login": enlace_login},
    )


def avisar_rechazo(nombre, email):
    """Avisa al solicitante que su solicitud no fue aprobada (la cuenta ya fue eliminada)."""
    _enviar("rechazo", email, "rechazo", {"nombre": nombre})
