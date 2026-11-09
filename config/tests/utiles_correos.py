"""Comprobaciones comunes de los correos con logo (`config/correos.py`)."""

from config.correos import CID_LOGO


def comprobar_html_con_logo(correo):
    """Verifica la alternativa HTML y el logo inline referenciado por cid; devuelve el HTML."""
    assert len(correo.alternatives) == 1
    html, tipo = correo.alternatives[0]
    assert tipo == "text/html"
    assert f'src="cid:{CID_LOGO}"' in html
    assert "<link" not in html and "<style" not in html  # sin CSS externo ni hojas

    mensaje = correo.message()
    partes = list(mensaje.walk())
    relacionados = [p for p in partes if p.get_content_type() == "multipart/related"]
    assert len(relacionados) == 1
    hijos = relacionados[0].get_payload()
    assert hijos[0].get_content_type() == "multipart/alternative"
    (logo,) = [p for p in partes if p.get_content_type() == "image/png"]
    assert logo["Content-ID"] == f"<{CID_LOGO}>"
    assert logo.get_content_disposition() == "inline"
    assert logo in hijos
    assert logo.get_payload(decode=True).startswith(b"\x89PNG")
    # El logo no es un adjunto del negocio.
    assert all(not getattr(a, "get_content_type", None) for a in correo.attachments)
    return html
