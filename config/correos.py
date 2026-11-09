"""Armado común de los correos de AquaLab: texto plano + alternativa HTML con el logo.

`armar_correo` devuelve un `CorreoAquaLab` (un `EmailMultiAlternatives`) con el cuerpo en texto
plano de siempre y una alternativa HTML simple (estilos inline, sin CSS externo) que muestra arriba
el logo de AquaLab como imagen inline (`cid:logo-aqualab`). Lo usan el aviso de desvíos
(`estudios/notificaciones.py`), el envío del informe (`informes/envios.py`) y la aprobación de
cuenta (`usuarios/notificaciones.py`).

Estructura MIME: `multipart/related` (alternativa texto/HTML + logo) y, si hay adjuntos (el PDF del
informe), todo eso dentro de un `multipart/mixed`. El logo no va en `attachments`: así esa lista
sigue teniendo solo los adjuntos del negocio.
"""

from email.mime.image import MIMEImage
from functools import lru_cache

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.mail import EmailMultiAlternatives
from django.core.mail.message import SafeMIMEMultipart
from django.template.loader import render_to_string

CID_LOGO = "logo-aqualab"
RUTA_LOGO = "img/marca/aqualab-horizontal.png"


@lru_cache(maxsize=1)
def bytes_del_logo():
    ruta = finders.find(RUTA_LOGO)
    with open(ruta, "rb") as archivo:
        return archivo.read()


def logo_inline():
    imagen = MIMEImage(bytes_del_logo(), "png")
    imagen.add_header("Content-ID", f"<{CID_LOGO}>")
    imagen.add_header("Content-Disposition", "inline", filename="aqualab.png")
    return imagen


class CorreoAquaLab(EmailMultiAlternatives):
    """Envuelve la alternativa texto/HTML en un `multipart/related` con el logo inline."""

    def _create_message(self, msg):
        alternativa = self._create_alternatives(msg)
        relacionado = SafeMIMEMultipart(
            _subtype="related", encoding=self.encoding or settings.DEFAULT_CHARSET
        )
        relacionado.attach(alternativa)
        relacionado.attach(logo_inline())
        return self._create_attachments(relacionado)


def asunto_de(plantilla, contexto):
    """El asunto en una sola línea."""
    return " ".join(render_to_string(plantilla, contexto).split())


def armar_correo(asunto, plantilla_texto, plantilla_html, contexto, *, to, from_email=None):
    """El correo con el texto plano de `plantilla_texto` y la alternativa HTML de
    `plantilla_html` (que extiende `correos/base.html`)."""
    cuerpo = render_to_string(plantilla_texto, contexto)
    html = render_to_string(plantilla_html, {**contexto, "cid_logo": CID_LOGO})
    correo = CorreoAquaLab(
        subject=asunto,
        body=cuerpo,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        to=to,
    )
    correo.attach_alternative(html, "text/html")
    return correo
