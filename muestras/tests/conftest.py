import pytest
from django.test import Client
from django.utils import timezone

from clientes.models import Cliente
from muestras.models import Muestra, Origen

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
def cliente_a():
    return Cliente.objects.create(
        razon_social="Aguas del Sur S.A.",
        tipo_documento="CUIT",
        numero_documento="20123456786",
        email="contacto@aguassur.com",
    )


@pytest.fixture
def cliente_b():
    return Cliente.objects.create(
        nombre="Juan Pérez",
        tipo_documento="DNI",
        numero_documento="30123456",
        email="juan@ejemplo.com",
    )


@pytest.fixture
def cliente_inactivo():
    return Cliente.objects.create(
        razon_social="Cooperativa Río Claro",
        tipo_documento="CUIT",
        numero_documento="30500010911",
        email="coop@ejemplo.com",
        activo=False,
    )


@pytest.fixture
def origen_a(cliente_a):
    return Origen.objects.create(cliente=cliente_a, nombre="Pozo N°2")


@pytest.fixture
def origen_b(cliente_b):
    return Origen.objects.create(cliente=cliente_b, nombre="Tanque elevado")


@pytest.fixture
def hoy():
    return timezone.localdate()


@pytest.fixture
def datos_muestra_validos(cliente_a, origen_a, hoy):
    """Datos de POST válidos para el formulario de registro de muestra."""
    return {
        "cliente": cliente_a.pk,
        "origen": origen_a.pk,
        "origen_nuevo": "",
        "fecha_muestreo": hoy.isoformat(),
        "fecha_ingreso": hoy.isoformat(),
        "sitio_extraccion": "Canilla de salida del tanque",
        "tipo_vertido": "agua",
        "nombre": "",
        "responsable_muestreo": "",
    }


@pytest.fixture
def crear_muestra(cliente_a, origen_a, empleado, hoy):
    """Crea una muestra válida con el N° PI indicado (para preparar el "último N° PI")."""

    def crear(numero_pi, **extra):
        datos = {
            "numero_pi": numero_pi,
            "cliente": cliente_a,
            "origen": origen_a,
            "fecha_muestreo": hoy,
            "fecha_ingreso": hoy,
            "sitio_extraccion": "Canilla de salida del tanque",
            "registrada_por": empleado,
        }
        datos.update(extra)
        return Muestra.objects.create(**datos)

    return crear
