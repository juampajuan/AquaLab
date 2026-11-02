import pytest
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import escape

from estudios.tests.utiles import cargar, validar
from informes.models import Informe
from informes.servicios import emitir_informe
from pruebas.models import Prueba

from .utiles import png

pytestmark = pytest.mark.django_db

CAMPOS_PRUEBA = ("nombre", "codigo", "resultado_texto", "limite_texto", "norma", "evaluacion_texto")


@pytest.fixture
def informe(estudio_de, empleado, bioquimico):
    estudio = estudio_de("PH", "CL-", "ECOLI", "SS10")
    # Cloruro es fórmula x*10: 40 → 400 mg/l. SS10 0,05 queda por debajo del LD 0,1.
    cargar(estudio, empleado, PH="7.4", CL_="40", ECOLI="0", SS10="0.05")
    validar(estudio, bioquimico, "PH", "CL-", "ECOLI", "SS10")
    return emitir_informe(estudio.pk, bioquimico)


def valores(contenido):
    """Todos los textos del contenido que el documento tiene que mostrar."""
    textos = [v for k, v in contenido["laboratorio"].items() if k != "logo"]
    textos += list(contenido["cliente"].values())
    textos += list(contenido["muestra"].values())
    textos += list(contenido["estudio"].values())
    for prueba in contenido["pruebas"]:
        textos += [prueba[campo] for campo in CAMPOS_PRUEBA]
    if "firma" in contenido:
        textos += [contenido["firma"]["nombre"], contenido["firma"]["matricula"]]
    return [t for t in textos if t]


def impreso(informe, pdf=True):
    contexto = {"informe": informe, "contenido": informe.contenido, "pdf": pdf}
    return render_to_string("informes/impreso.html", contexto)


def sin_firma(informe):
    contenido = {k: v for k, v in informe.contenido.items() if k != "firma"}
    Informe.objects.filter(pk=informe.pk).update(contenido=contenido)
    informe.refresh_from_db()
    return informe


def test_impreso_contiene_todo_el_contenido(informe):
    html = impreso(informe)
    for texto in valores(informe.contenido):
        assert escape(texto) in html, texto
    assert "INF-000001" in html
    assert informe.fecha_emision.astimezone().strftime("%d/%m/%Y") in html
    assert "< 0,1" in informe.contenido["pruebas"][-1]["resultado_texto"] or "&lt; 0,1" in html
    fila_cloruro = html[html.index("CL-") - 600 : html.index("CL-")]
    assert "inf-fuera" in fila_cloruro


def test_pantalla_contiene_todo_el_contenido(cliente_http, informe):
    html = cliente_http.get(reverse("informes:ver", args=[informe.estudio_id])).content.decode()
    for texto in valores(informe.contenido):
        assert escape(texto) in html, texto


def test_impreso_con_firma(informe):
    html = impreso(informe)
    firma = informe.contenido["firma"]
    assert f'src="{firma["imagen"]}"' in html
    assert escape(firma["nombre"]) in html
    assert "Mat. MP 1234" in html
    assert "Sin firma registrada" not in html


def test_sin_firma_registrada(cliente_http, informe):
    sin_firma(informe)
    assert "Sin firma registrada" in impreso(informe)
    pantalla = cliente_http.get(reverse("informes:ver", args=[informe.estudio_id]))
    assert "Sin firma registrada" in pantalla.content.decode()


def test_imprimir_pagina_independiente(cliente_http, informe):
    respuesta = cliente_http.get(reverse("informes:imprimir", args=[informe.estudio_id]))
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert html.lstrip().lower().startswith("<!doctype html>")
    assert '<link rel="stylesheet" href="/static/css/informe.css"' in html
    assert "informes/imprimir.js" in html
    assert 'class="inf-barra"' in html
    assert "Imprimir" in html and "Volver al informe" in html
    assert reverse("informes:ver", args=[informe.estudio_id]) in html
    assert "data-menu-navegacion" not in html


def test_impreso_para_pdf_sin_barra_ni_script(informe):
    html = impreso(informe, pdf=True)
    assert "inf-barra" not in html
    assert "<link" not in html
    assert "imprimir.js" not in html


def test_exportacion_no_cambia_al_editar(informe, bioquimico, settings, cliente_http):
    antes = impreso(informe)
    cliente = informe.estudio.muestra.cliente
    cliente.domicilio = "Domicilio nuevo 999"
    cliente.save()
    Prueba.objects.filter(codigo="CL-").update(limite_max="999")
    settings.AQUALAB_LABORATORIO = settings.AQUALAB_LABORATORIO | {"nombre": "Laboratorio nuevo"}
    firma = bioquimico.firma_profesional
    firma.imagen = png(300, 100)
    firma.matricula = "MP 9999"
    firma.save()
    informe.refresh_from_db()
    despues = impreso(informe)
    assert despues == antes
    for nuevo in ("Domicilio nuevo 999", "999", "Laboratorio nuevo", "MP 9999"):
        assert f">{nuevo}<" not in despues
    pagina = cliente_http.get(reverse("informes:imprimir", args=[informe.estudio_id]))
    assert "Laboratorio nuevo" not in pagina.content.decode()
