"""PDF del informe emitido (US 7.3), generado con WeasyPrint.

Sale siempre de la copia guardada (`Informe.contenido`, FR-006) con el mismo template que la
impresión del navegador (`informes/impreso.html`) y la hoja `static/css/informe.css`.
"""

from pathlib import Path

import weasyprint
from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from weasyprint.text.fonts import FontConfiguration


def documento(informe):
    """El documento de WeasyPrint ya paginado (A4)."""
    html = render_to_string(
        "informes/impreso.html",
        {
            "informe": informe,
            "contenido": informe.contenido,
            "pdf": True,
            # WeasyPrint lee el recurso local, sin depender de un servidor HTTP de estáticos.
            "logo_pdf": Path(finders.find("img/marca/aqualab-isotipo.png")).as_uri(),
        },
    )
    # Sin FontConfiguration, WeasyPrint ignora los @font-face (la fuente Inter de la hoja).
    fuentes = FontConfiguration()
    hoja = weasyprint.CSS(filename=finders.find("css/informe.css"), font_config=fuentes)
    return weasyprint.HTML(string=html, base_url=str(settings.BASE_DIR)).render(
        stylesheets=[hoja], font_config=fuentes
    )


def generar_pdf(informe):
    return documento(informe).write_pdf()
