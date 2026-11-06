import logging
from pathlib import Path
from unittest import mock

import pytest
from django.conf import settings
from django.contrib.messages import get_messages
from django.urls import reverse

from informes import pdf
from informes.models import Informe

pytestmark = pytest.mark.django_db

# WeasyPrint mide las páginas en px CSS (96 por pulgada): 210 × 297 mm.
A4 = (210 / 25.4 * 96, 297 / 25.4 * 96)


@pytest.fixture
def informe(estudio_de, empleado, completar, bioquimico):
    from informes.servicios import emitir_informe

    estudio = estudio_de("PH", "CL-")
    completar(estudio)
    return emitir_informe(estudio.pk, bioquimico)


def es_a4(pagina):
    return abs(pagina.width - A4[0]) < 1 and abs(pagina.height - A4[1]) < 1


def test_ver_ofrece_pdf_e_imprimir(cliente_http, informe):
    html = cliente_http.get(reverse("informes:ver", args=[informe.estudio_id])).content.decode()
    assert f'href="{reverse("informes:pdf", args=[informe.estudio_id])}"' in html
    assert "Descargar PDF" in html
    imprimir = reverse("informes:imprimir", args=[informe.estudio_id])
    inicio = html.index(f'href="{imprimir}"')
    assert 'target="_blank"' in html[inicio - 200 : inicio + 200]


@pytest.mark.parametrize("nombre", ["informes:pdf", "informes:imprimir"])
def test_exportar_sin_informe_404(cliente_http, estudio_de, nombre):
    estudio = estudio_de("PH")
    assert cliente_http.get(reverse(nombre, args=[estudio.pk])).status_code == 404
    assert cliente_http.get(reverse(nombre, args=[999999])).status_code == 404


def test_pdf_descarga_a4(cliente_http, informe, caplog):
    respuesta = cliente_http.get(reverse("informes:pdf", args=[informe.estudio_id]))
    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == "application/pdf"
    assert respuesta["Content-Disposition"] == 'attachment; filename="INF-000001.pdf"'
    assert respuesta.content.startswith(b"%PDF-")
    documento = pdf.documento(informe)
    assert documento.pages
    assert all(es_a4(p) for p in documento.pages)
    # Un PNG sin resolver no impide generar un PDF: WeasyPrint solo registra el error.
    assert not any("Failed to load image" in r.getMessage() for r in caplog.records)


def test_pdf_sale_de_impreso(informe):
    with mock.patch("informes.pdf.render_to_string", wraps=pdf.render_to_string) as render:
        pdf.generar_pdf(informe)
    plantilla, contexto = render.call_args.args
    assert plantilla == "informes/impreso.html"
    assert contexto["pdf"] is True
    assert contexto["contenido"] == informe.contenido
    assert contexto["informe"] == informe


def test_sin_firma_registrada_en_pdf(informe):
    contenido = {k: v for k, v in informe.contenido.items() if k != "firma"}
    Informe.objects.filter(pk=informe.pk).update(contenido=contenido)
    informe.refresh_from_db()
    assert pdf.generar_pdf(informe).startswith(b"%PDF-")


def test_pdf_varias_hojas(informe):
    prueba = {
        "unidad": "mg/l",
        "resultado": "400",
        "resultado_texto": "400",
        "limite_texto": "máx. 350.0",
        "limite_min": "",
        "limite_max": "350.0",
        "norma": "Ley 24.051",
        "origen_limites": "general",
        "limite_deteccion": "1",
        "evaluacion": "fuera_de_norma",
        "evaluacion_texto": "Fuera de norma",
    }
    contenido = informe.contenido | {
        "pruebas": [prueba | {"codigo": f"P{i:02d}", "nombre": f"Prueba {i}"} for i in range(80)]
    }
    Informe.objects.filter(pk=informe.pk).update(contenido=contenido)
    informe.refresh_from_db()
    documento = pdf.documento(informe)
    assert len(documento.pages) > 1
    assert all(es_a4(p) for p in documento.pages)


def test_hoja_de_estilos_paged_media():
    css = (Path(settings.BASE_DIR) / "static" / "css" / "informe.css").read_text()
    for regla in (
        "size: A4",
        "counter(page)",
        "counter(pages)",
        "string(numero)",
        "break-inside: avoid",
        "table-header-group",
    ):
        assert regla in css, regla


def test_exportar_no_modifica(cliente_http, informe):
    estudio = informe.estudio
    antes = (informe.contenido, informe.fecha_emision, estudio.estado)
    cliente_http.get(reverse("informes:pdf", args=[estudio.pk]))
    cliente_http.get(reverse("informes:imprimir", args=[estudio.pk]))
    informe.refresh_from_db()
    estudio.refresh_from_db()
    assert (informe.contenido, informe.fecha_emision, estudio.estado) == antes


def test_pdf_error_redirige(cliente_http, informe, caplog):
    url_ver = reverse("informes:ver", args=[informe.estudio_id])
    with (
        mock.patch("informes.pdf.generar_pdf", side_effect=Exception("falla")),
        caplog.at_level(logging.ERROR, logger="informes"),
    ):
        respuesta = cliente_http.get(reverse("informes:pdf", args=[informe.estudio_id]))
    assert respuesta.status_code == 302
    assert respuesta.url == url_ver
    mensajes = [str(m) for m in get_messages(respuesta.wsgi_request)]
    assert mensajes == ["No se pudo generar el PDF. Intentá nuevamente."]
    assert any(r.name == "informes" for r in caplog.records)
