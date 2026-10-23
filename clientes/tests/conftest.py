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
def otro_cliente():
    return Cliente.objects.create(
        nombre="Juan Pérez",
        tipo_documento="DNI",
        numero_documento="30123456",
        email="juan@ejemplo.com",
        telefono="+54 11 4321-5678",
        domicilio="Av. Corrientes 1234",
    )


@pytest.fixture
def datos_edicion_validos():
    return {
        "nombre": "Roberto Gómez",
        "razon_social": "Aguas del Sur S.A.",
        "tipo_documento": "CUIT",
        "numero_documento": "20-12345678-6",
        "email": "nuevo@aguassur.com",
        "telefono": "+54 11 5555-6666",
        "domicilio": "Av. Paseo Colón 850",
    }


@pytest.fixture
def en_revision(cliente_autenticado, datos_cliente_empresa):
    """Deja el alta de cliente en revisión: los datos quedan en `session["cliente_pendiente"]`."""
    cliente_autenticado.post(reverse("clientes:registrar"), datos_cliente_empresa)
    return cliente_autenticado


@pytest.fixture
def clientes_busqueda():
    """Clientes para las pruebas de búsqueda (US 3.1)."""
    datos = [
        {"nombre": "Juan Pérez", "tipo_documento": "DNI", "numero_documento": "30123456"},
        {
            "razon_social": "Aguas del Sur S.A.",
            "tipo_documento": "CUIT",
            "numero_documento": "20123456786",
        },
        {
            "razon_social": "Cooperativa Río Claro",
            "tipo_documento": "CUIT",
            "numero_documento": "30500010911",
        },
        {"nombre": "Lucía Fernández", "tipo_documento": "DNI", "numero_documento": "28999111"},
        {"nombre": "María Gómez", "tipo_documento": "DNI", "numero_documento": "20111222"},
        {"nombre": "María Gómez", "tipo_documento": "DNI", "numero_documento": "27333444"},
    ]
    return [
        Cliente.objects.create(email=f"cliente{i}@ejemplo.com", **d) for i, d in enumerate(datos)
    ]
