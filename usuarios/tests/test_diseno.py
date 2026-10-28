"""Estructura de la interfaz del registro de usuario (SCRUM-67, US2)."""

import pytest
from django.urls import reverse

from config.tests.ayudas_diseno import es_obligatorio, tiene_componentes_de_confirmacion

pytestmark = pytest.mark.django_db


def test_crear_cuenta_marca_todos_los_campos_como_obligatorios(client):
    html = client.get(reverse("usuarios:registro")).content.decode()

    for campo in ("first_name", "last_name", "email", "password1", "password2"):
        assert es_obligatorio(html, campo), campo


def test_confirmacion_usa_los_componentes_comunes_sin_la_contrasena(en_revision, password_registro):
    html = en_revision.get(reverse("usuarios:registro_confirmar")).content.decode()

    assert tiene_componentes_de_confirmacion(html)
    assert password_registro not in html
