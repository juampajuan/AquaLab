import pytest
from django.test import Client
from django.urls import reverse

PASSWORD_REGISTRO = "Clave-Secreta-Unica-987"
PASSWORD_EXISTENTE = "Clave-Existente-Segura-654"


@pytest.fixture
def password_registro():
    return PASSWORD_REGISTRO


@pytest.fixture
def datos_registro(password_registro):
    return {
        "first_name": "Ana",
        "last_name": "Pérez",
        "email": "ana@lab.com",
        "password1": password_registro,
        "password2": password_registro,
    }


@pytest.fixture
def usuario_pendiente(django_user_model):
    return django_user_model.objects.create_user(
        email="pendiente@lab.com",
        password=PASSWORD_EXISTENTE,
        first_name="Pedro",
        last_name="Gómez",
        is_active=False,
    )


@pytest.fixture
def usuario_aprobado(django_user_model):
    return django_user_model.objects.create_user(
        email="aprobado@lab.com",
        password=PASSWORD_EXISTENTE,
        first_name="Pedro",
        last_name="Gómez",
        is_active=True,
    )


@pytest.fixture
def administrador(django_user_model):
    return django_user_model.objects.create_superuser(
        email="admin@lab.com",
        password=PASSWORD_EXISTENTE,
        first_name="Admin",
        last_name="AquaLab",
    )


@pytest.fixture
def cliente_admin(administrador):
    cliente = Client()
    cliente.force_login(administrador)
    return cliente


@pytest.fixture
def en_revision(client, datos_registro):
    """Deja el registro en revisión: los datos quedan en `session["registro_pendiente"]`."""
    client.post(reverse("usuarios:registro"), datos_registro)
    return client


@pytest.fixture
def cliente_csrf():
    return Client(enforce_csrf_checks=True)
