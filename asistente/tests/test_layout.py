"""Botón y panel del asistente en el layout (US1 Esc. 1, US4 Esc. 3)."""

import re

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def boton(html):
    encontrado = re.search(r"<button[^>]*data-asistente-abrir[^>]*>", html)
    assert encontrado, "Falta el botón del asistente"
    return encontrado.group(0)


def test_boton_y_panel_con_sesion(cliente_http, config_asistente):
    html = cliente_http.get(reverse("inicio")).content.decode()
    assert "aria-disabled" not in boton(html)
    panel = re.search(r"<section[^>]*data-asistente(?:\s|>)[^>]*>", html).group(0)
    assert 'role="dialog"' in panel
    assert 'aria-label="Asistente"' in panel
    assert f'data-url="{reverse("asistente:preguntar")}"' in panel
    assert "hidden" in panel
    assert re.search(r'<textarea[^>]*maxlength="500"', html)
    assert re.search(r'aria-live="polite"', html)
    for ejemplo in (
        "¿Cómo está el PI 200417?",
        "¿Qué estudios tiene Lácteos del Sur?",
        "¿Qué no cumple en el estudio de la escuela N° 12?",
        "Registrá una muestra de Lácteos del Sur, pozo 2",
    ):
        assert ejemplo in html
    assert "pedime que prepare el registro de una muestra o un estudio" in html
    assert "no cambio nada" not in html
    # Botón de envío con el ícono de enviar (Lucide send-horizontal) y nombre accesible.
    enviar = re.search(r"<button[^>]*data-asistente-enviar[^>]*>(.*?)</button>", html, re.S)
    assert 'aria-label="Enviar pregunta"' in enviar.group(0)
    assert "M6 12h16" in enviar.group(1)


@pytest.mark.parametrize("ruta", ["usuarios:login", "usuarios:registro"])
def test_sin_sesion_no_hay_asistente(client, config_asistente, ruta):
    html = client.get(reverse(ruta)).content.decode()
    assert "data-asistente" not in html


def test_sin_clave_deshabilitado(cliente_http, settings):
    settings.ASISTENTE = {"clave": ""}
    html = cliente_http.get(reverse("inicio")).content.decode()
    assert 'aria-disabled="true"' in boton(html)
    assert "El asistente no está configurado" in html


@pytest.mark.parametrize("clave", ["", "clave-test"])
@pytest.mark.parametrize("ruta", ["inicio", "estudios:buscar", "clientes:buscar"])
def test_pantallas_funcionan_con_o_sin_clave(cliente_http, settings, clave, ruta):
    settings.ASISTENTE = {"clave": clave}
    assert cliente_http.get(reverse(ruta)).status_code == 200


def test_cerrar_sesion_borra_la_conversacion(cliente_http, config_asistente):
    """El formulario de cerrar sesión lleva el gancho con el que aqualab.js borra la conversación
    guardada en sessionStorage (FR-019)."""
    html = cliente_http.get(reverse("inicio")).content.decode()
    formulario = re.search(rf'<form[^>]*action="{reverse("usuarios:logout")}"[^>]*>', html).group(0)
    assert "data-cerrar-sesion" in formulario
