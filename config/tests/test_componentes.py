"""Componentes compartidos de la interfaz (SCRUM-67, US2 escenario 5)."""

import re

import pytest
from django.contrib.messages import constants
from django.contrib.messages.storage.base import Message
from django.template.loader import render_to_string


@pytest.mark.parametrize(
    ("nivel", "esperado"),
    [
        (constants.SUCCESS, "exito"),
        (constants.ERROR, "error"),
        (constants.WARNING, "advertencia"),
        (constants.INFO, "info"),
    ],
)
def test_cada_mensaje_se_dibuja_segun_su_nivel_y_se_puede_cerrar(nivel, esperado):
    html = render_to_string("ui/mensajes.html", {"messages": [Message(nivel, "Texto de prueba")]})

    aviso = re.search(r'<div[^>]*data-nivel="([^"]+)"[^>]*>(.*?)</button>', html, re.S)
    assert aviso.group(1) == esperado
    assert "Texto de prueba" in aviso.group(2)
    assert "data-cerrar-mensaje" in aviso.group(2)


def test_sin_mensajes_no_dibuja_nada():
    assert render_to_string("ui/mensajes.html", {"messages": []}).strip() == ""
