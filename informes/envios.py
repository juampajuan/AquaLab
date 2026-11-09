"""Envío del informe emitido por correo (SCRUM-79).

`enviar_informe` es el único envío: lo llama `informes:enviar` al confirmar. Es sincrónico, así el
usuario sabe en el momento si salió, y cada intento queda en `EnvioInforme`. Una falla de correo o
de PDF nunca se propaga: se registra como «fallido» y queda en el log `informes.envios`.
"""

import logging
from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import Http404
from django.template.loader import render_to_string

from .models import EnvioInforme, Informe, ResultadoEnvio
from .pdf import generar_pdf

logger = logging.getLogger("informes.envios")

PERMISO = "informes.emitir_informes"


@dataclass(frozen=True)
class ResultadoDelEnvio:
    envio: EnvioInforme
    duplicado: bool = False


def mensaje_de_correo(informe, destinatario, pdf):
    """El correo al cliente, con el texto armado desde la copia del informe y el PDF adjunto."""
    contexto = {"numero": informe.numero_mostrado, "contenido": informe.contenido}
    asunto = " ".join(render_to_string("informes/correos/informe_asunto.txt", contexto).split())
    cuerpo = render_to_string("informes/correos/informe_cuerpo.txt", contexto)
    mensaje = EmailMessage(
        subject=asunto, body=cuerpo, from_email=settings.DEFAULT_FROM_EMAIL, to=[destinatario]
    )
    mensaje.attach(f"{informe.numero_mostrado}.pdf", pdf, "application/pdf")
    return mensaje


def ultimo_envio_exitoso(informe):
    return informe.envios.filter(resultado=ResultadoEnvio.ENVIADO).first()


def enviar_informe(estudio_pk, usuario, clave):
    """Envía el informe del estudio al correo actual del cliente y registra el intento.

    Bloquea la fila del `Informe` (sin modificarla) para que dos pedidos con la misma `clave` no
    envíen dos correos: el segundo encuentra el envío ya registrado y lo devuelve como duplicado.
    """
    if not usuario.has_perm(PERMISO):
        raise PermissionDenied
    with transaction.atomic():
        try:
            informe = (
                Informe.objects.select_for_update()
                .select_related("estudio__muestra__cliente")
                .get(estudio__pk=estudio_pk)
            )
        except Informe.DoesNotExist as exc:
            raise Http404 from exc
        previo = EnvioInforme.objects.filter(clave=clave).first()
        if previo is not None:
            return ResultadoDelEnvio(previo, duplicado=True)
        destinatario = informe.estudio.muestra.cliente.email
        try:
            mensaje_de_correo(informe, destinatario, generar_pdf(informe)).send(fail_silently=False)
            resultado = ResultadoEnvio.ENVIADO
        except Exception:
            logger.exception(
                "No se pudo enviar el informe %s a %s", informe.numero_mostrado, destinatario
            )
            resultado = ResultadoEnvio.FALLIDO
        envio = EnvioInforme.objects.create(
            informe=informe,
            enviado_por=usuario,
            destinatario=destinatario,
            resultado=resultado,
            clave=clave,
        )
    return ResultadoDelEnvio(envio)
