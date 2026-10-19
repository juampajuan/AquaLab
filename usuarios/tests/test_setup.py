import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_inicio_sin_sesion_redirige_al_login(client):
    respuesta = client.get(reverse("inicio"))

    assert respuesta.status_code == 302
    assert respuesta.url.startswith(reverse("admin:login"))


def test_create_user_normaliza_el_email():
    usuario = get_user_model().objects.create_user(
        email="  Ana.Perez@Ejemplo.COM ",
        password="clave-segura-123",
        first_name="Ana",
        last_name="Pérez",
    )

    assert usuario.email == "ana.perez@ejemplo.com"
    assert usuario.check_password("clave-segura-123")


def test_create_superuser_crea_usuario_activo_y_staff():
    admin = get_user_model().objects.create_superuser(
        email="admin@ejemplo.com",
        password="clave-segura-123",
        first_name="Admin",
        last_name="AquaLab",
    )

    assert admin.is_active
    assert admin.is_staff
    assert admin.is_superuser
