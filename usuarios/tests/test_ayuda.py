"""Ayuda en formularios (US 9.1) en el registro y el login."""

import re

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_los_requisitos_de_contrasena_siguen_visibles_y_sin_icono(client):
    html = client.get(reverse("usuarios:registro")).content.decode()

    requisitos = re.search(
        r'<div class="campo-ayuda" id="id_password1_helptext">(.*?)</div>', html, re.S
    )
    assert requisitos and requisitos[1].strip()
    assert re.search(
        r'<input[^>]*name="password1"[^>]*aria-describedby="id_password1_helptext"', html
    )
    assert "data-ayuda" not in html


@pytest.mark.django_db
def test_los_campos_obvios_del_registro_no_tienen_ayuda(client):
    html = client.get(reverse("usuarios:registro")).content.decode()

    for nombre in ("first_name", "last_name", "email"):
        assert f'id="id_{nombre}_helptext"' not in html


@pytest.mark.django_db
@pytest.mark.parametrize("ruta", ["usuarios:login", "usuarios:registro"])
def test_los_layouts_cargan_el_comportamiento_de_la_ayuda(client, ruta):
    html = client.get(reverse(ruta)).content.decode()

    assert "js/aqualab.js" in html
    if ruta == "usuarios:login":
        assert "data-ayuda" not in html
