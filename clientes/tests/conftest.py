import pytest
from django.test import Client
from django.urls import reverse

from clientes.models import Cliente

PASSWORD_EMPLEADO = "Clave-Valida-123"


@pytest.fixture
def empleado(django_user_model):
    return django_user_model.objects.create_user(
        email="empleado@lab.com",
        password=PASSWORD_EMPLEADO,
        first_name="Laura",
        last_name="Martínez",
        is_active=True,
    )


@pytest.fixture
def cliente_autenticado(empleado):
    cliente = Client()
    cliente.force_login(empleado)
    return cliente


@pytest.fixture
def datos_cliente_persona():
    return {
        "nombre": "Juan Pérez",
        "razon_social": "",
        "tipo_documento": "DNI",
        "numero_documento": "30.123.456",
        "email": "juan@ejemplo.com",
        "telefono": "+54 11 4321-5678",
        "domicilio": "Av. Corrientes 1234",
    }


@pytest.fixture
def datos_cliente_empresa():
    return {
        "nombre": "",
        "razon_social": "Aguas del Sur S.A.",
        "tipo_documento": "CUIT",
        "numero_documento": "20-12345678-6",
        "email": "contacto@aguassur.com",
        "telefono": "",
        "domicilio": "",
    }


@pytest.fixture
def cliente_existente():
    return Cliente.objects.create(
        razon_social="Aguas del Sur S.A.",
        tipo_documento="CUIT",
        numero_documento="20123456786",
        email="contacto@aguassur.com",
    )


@pytest.fixture
def en_revision(cliente_autenticado, datos_cliente_empresa):
    """Deja el alta de cliente en revisión: los datos quedan en `session["cliente_pendiente"]`."""
    cliente_autenticado.post(reverse("clientes:registrar"), datos_cliente_empresa)
    return cliente_autenticado
