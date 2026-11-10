"""Próximo paso en la ficha del estudio (SCRUM-82): una sola acción principal según el estado."""

import re

import pytest
from django.urls import reverse

from estudios.tests.utiles import cargar, validar

pytestmark = pytest.mark.django_db


def ficha(cliente, estudio):
    return cliente.get(reverse("estudios:detalle", args=[estudio.pk])).content.decode()


def paso(html):
    bloque = re.search(
        r'data-componente="proximo-paso" data-accion="([^"]*)"(.*?)</div>\s*</div>', html, re.S
    )
    assert bloque, "no se encontró el próximo paso"
    return bloque.group(1), bloque.group(2)


def principal(html):
    """El href del botón principal, o None si no hay."""
    encontrado = re.search(
        r'<a href="([^"]+)" class="btn btn-primario" data-accion-principal>', html
    )
    return encontrado.group(1) if encontrado else None


def test_pendiente_propone_cargar_mediciones(cliente_http, estudio_de):
    estudio = estudio_de("PH", "CL-")
    html = ficha(cliente_http, estudio)

    accion, texto = paso(html)
    assert accion == "cargar"
    assert "Falta cargar la medición de 2 pruebas." in texto
    assert principal(html) == reverse("estudios:cargar_mediciones", args=[estudio.pk])
    # Agregar prueba queda como secundaria.
    assert re.search(
        r'class="btn btn-secundario">\s*<svg[^>]*>.*?</svg>\s*Agregar prueba', html, re.S
    )


def test_cargado_sin_permiso_espera_validacion(cliente_http, empleado, estudio_de):
    estudio = estudio_de("PH")
    cargar(estudio, empleado, PH="7.4")
    html = ficha(cliente_http, estudio)

    accion, texto = paso(html)
    assert accion == ""
    assert "esperan la validación de un bioquímico" in texto
    assert principal(html) is None


def test_cargado_bioquimico_propone_validar(cliente_bioquimico, bioquimico, estudio_de):
    estudio = estudio_de("PH")
    cargar(estudio, bioquimico, PH="7.4")
    html = ficha(cliente_bioquimico, estudio)

    assert paso(html)[0] == "validar"
    assert principal(html) == reverse("estudios:validar_resultados", args=[estudio.pk])


def test_validar_secundario_mientras_falta_medir(cliente_bioquimico, bioquimico, estudio_de):
    estudio = estudio_de("PH", "CL-")
    cargar(estudio, bioquimico, PH="7.4")
    html = ficha(cliente_bioquimico, estudio)

    assert paso(html)[0] == "cargar"
    validar_url = reverse("estudios:validar_resultados", args=[estudio.pk])
    assert f'<a href="{validar_url}" class="btn btn-secundario">' in html


def test_finalizado_propone_generar_informe(cliente_bioquimico, bioquimico, estudio_de):
    estudio = estudio_de("PH")
    cargar(estudio, bioquimico, PH="7.4")
    validar(estudio, bioquimico, "PH")
    html = ficha(cliente_bioquimico, estudio)

    assert paso(html)[0] == "generar_informe"
    assert principal(html) == reverse("informes:vista_previa", args=[estudio.pk])


def test_informe_emitido_propone_verlo(cliente_bioquimico, bioquimico, estudio_de):
    from informes.servicios import emitir_informe

    estudio = estudio_de("PH")
    cargar(estudio, bioquimico, PH="7.4")
    validar(estudio, bioquimico, "PH")
    emitir_informe(estudio.pk, bioquimico)
    html = ficha(cliente_bioquimico, estudio)

    assert paso(html)[0] == "ver_informe"
    assert principal(html) == reverse("informes:ver", args=[estudio.pk])


def test_sin_datos_repetidos_ni_navegacion_de_mas(cliente_http, estudio_de):
    html = ficha(cliente_http, estudio_de("PH"))

    for texto in ("Estado general", "Identificador", "Ver ficha de la muestra", "Buscar estudios"):
        assert texto not in html, texto
    # Un solo botón principal (no cuenta el «Reintentar» oculto de la guardia de sesión).
    contenido = html.split('id="sesion-reintentar"')[0]
    assert contenido.count('class="btn btn-primario"') == 1
