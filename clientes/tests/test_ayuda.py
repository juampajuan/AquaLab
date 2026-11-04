"""Ayuda en formularios (US 9.1): registro y edición de cliente."""

import re

import pytest
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db

CON_AYUDA = ("razon_social", "tipo_documento", "numero_documento", "email")
SIN_AYUDA = ("nombre", "telefono", "domicilio")


def tooltip(html, nombre):
    encontrado = re.search(
        rf'<span role="tooltip" id="id_{nombre}_helptext"[^>]*>(.*?)</span>', html
    )
    return encontrado[1].strip() if encontrado else None


@pytest.fixture
def pantallas(cliente_autenticado, cliente_existente):
    return {
        "registrar": cliente_autenticado.get(reverse("clientes:registrar")).content.decode(),
        "editar": cliente_autenticado.get(
            reverse("clientes:editar", args=[cliente_existente.pk])
        ).content.decode(),
    }


@pytest.mark.parametrize("pantalla", ["registrar", "editar"])
@pytest.mark.parametrize("nombre", CON_AYUDA)
def test_campos_que_no_se_explican_solos_tienen_ayuda(pantallas, pantalla, nombre):
    assert tooltip(pantallas[pantalla], nombre)


@pytest.mark.parametrize("pantalla", ["registrar", "editar"])
@pytest.mark.parametrize("nombre", SIN_AYUDA)
def test_campos_obvios_no_tienen_ayuda(pantallas, pantalla, nombre):
    assert f'id="id_{nombre}_helptext"' not in pantallas[pantalla]


def test_el_tipo_de_documento_describe_al_grupo_de_opciones(pantallas):
    assert '<fieldset aria-describedby="id_tipo_documento_helptext">' in pantallas["registrar"]


def test_el_admin_no_cambia(django_user_model):
    administrador = django_user_model.objects.create_superuser(
        email="admin-ayuda@lab.com", password="ClaveSegura-123"
    )
    cliente = Client()
    cliente.force_login(administrador)

    respuesta = cliente.get("/admin/clientes/cliente/add/")
    assert respuesta.status_code == 200
    assert "data-ayuda" not in respuesta.content.decode()
