import uuid

import pytest
from django.utils import timezone


@pytest.fixture
def empleado(django_user_model):
    return django_user_model.objects.create_user(
        email="test-pruebas@ejemplo.com",
        password="Clave-Valida-123",
        first_name="Test",
        is_active=True,
    )


@pytest.fixture
def muestra(empleado):
    from clientes.models import Cliente
    from muestras.models import Muestra, Origen

    cliente = Cliente.objects.create(
        nombre="Cliente de test",
        tipo_documento="DNI",
        numero_documento="30123457",
        email="test-pruebas@ejemplo.com",
    )
    origen = Origen.objects.create(cliente=cliente, nombre="Origen de test")
    return Muestra.objects.create(
        numero_pi=200001,
        nombre="Muestra test",
        cliente=cliente,
        origen=origen,
        fecha_muestreo=timezone.localdate(),
        fecha_ingreso=timezone.localdate(),
        sitio_extraccion="Sitio test",
        registrada_por=empleado,
    )


@pytest.fixture
def prueba_en_tipo():
    from estudios.models import TipoEstudio
    from pruebas.models import Prueba

    prueba = Prueba.objects.create(codigo="USO-T", nombre="Prueba en tipo")
    tipo = TipoEstudio.objects.create(nombre="Tipo con prueba en uso")
    tipo.pruebas.set([prueba])
    return prueba


@pytest.fixture
def prueba_en_estudio(muestra, empleado):
    from estudios.models import TipoEstudio, TipoEstudioPrueba
    from estudios.servicios import crear_estudio
    from pruebas.models import Prueba

    prueba = Prueba.objects.create(codigo="USO-E", nombre="Prueba en estudio")
    tipo = TipoEstudio.objects.create(nombre="Tipo del estudio")
    tipo.pruebas.set([prueba])
    datos = {
        "clave": str(uuid.uuid4()),
        "muestra": muestra.pk,
        "tipo": tipo.pk,
        "version": tipo.version,
    }
    crear_estudio(datos, empleado)
    # Solo el estudio la usa: así se prueba ese caso por separado del tipo.
    TipoEstudioPrueba.objects.filter(tipo=tipo).delete()
    return prueba


@pytest.fixture
def prueba_libre():
    from pruebas.models import Prueba

    return Prueba.objects.create(codigo="LIBRE", nombre="Prueba libre")
