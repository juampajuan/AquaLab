import uuid

import pytest
from django.db import transaction
from django.test import Client
from django.utils import timezone


@pytest.fixture
def empleado(django_user_model):
    return django_user_model.objects.create_user(
        email="test-estudio@ejemplo.com",
        password="Clave-Valida-123",
        first_name="Test",
        is_active=True,
    )


@pytest.fixture
def cliente_a():
    from clientes.models import Cliente

    return Cliente.objects.create(
        nombre="Cliente de test",
        tipo_documento="DNI",
        numero_documento="30123456",
        email="test@ejemplo.com",
    )


@pytest.fixture
def muestra(cliente_a, empleado):
    from muestras.models import Muestra, Origen

    origen = Origen.objects.create(cliente=cliente_a, nombre="Origen de test")
    return Muestra.objects.create(
        numero_pi=200001,
        nombre="Muestra test",
        cliente=cliente_a,
        origen=origen,
        fecha_muestreo=timezone.localdate(),
        fecha_ingreso=timezone.localdate(),
        sitio_extraccion="Sitio test",
        registrada_por=empleado,
    )


@pytest.fixture
def pruebas():
    from pruebas.models import Prueba

    return [
        Prueba.objects.create(codigo="TEST-A", nombre="Prueba de test A"),
        Prueba.objects.create(codigo="TEST-B", nombre="Prueba de test B"),
    ]


@pytest.fixture
def tipo(pruebas):
    from estudios.models import TipoEstudio

    t = TipoEstudio.objects.create(nombre="Tipo de test", descripcion="Descripción test")
    t.pruebas.set(pruebas)
    return t


@pytest.fixture
def datos(muestra, tipo):
    return {
        "clave": str(uuid.uuid4()),
        "muestra": muestra.pk,
        "tipo": tipo.pk,
        "version": tipo.version,
    }


@pytest.fixture
def cliente_http(empleado):
    c = Client()
    c.force_login(empleado)
    return c


@pytest.fixture
def cambiar_tipo():
    # Escritor exclusivamente de test: no implementa la gestión de US 5.5.
    def cambiar(tipo, **cambios):
        from estudios.models import TipoEstudio

        with transaction.atomic():
            actual = TipoEstudio.objects.select_for_update().get(pk=tipo.pk)
            ids = cambios.pop("pruebas", None)
            cambio = False
            for campo, valor in cambios.items():
                if getattr(actual, campo) != valor:
                    setattr(actual, campo, valor)
                    cambio = True
            if ids is not None and set(actual.pruebas.values_list("pk", flat=True)) != set(ids):
                assert ids
                actual.pruebas.set(ids)
                cambio = True
            if cambio:
                actual.version += 1
                actual.save()
            return actual

    return cambiar


@pytest.fixture
def gestor(empleado):
    from django.contrib.auth.models import Permission

    empleado.user_permissions.add(Permission.objects.get(codename="gestionar_catalogo"))
    return empleado


@pytest.fixture
def staff_sin_permiso(django_user_model):
    return django_user_model.objects.create_user(
        email="staff-us55@ejemplo.com", password="Clave-Valida-123", is_active=True, is_staff=True
    )


@pytest.fixture
def tipo_inactivo(tipo):
    tipo.activo = False
    tipo.save()
    return tipo


@pytest.fixture
def otro_gestor(django_user_model):
    from django.contrib.auth.models import Permission

    usuario = django_user_model.objects.create_user(
        email="otro-gestor-us55@ejemplo.com", password="Clave-Valida-123", is_active=True
    )
    usuario.user_permissions.add(Permission.objects.get(codename="gestionar_catalogo"))
    return usuario


@pytest.fixture
def estudio(datos, empleado):
    from estudios.servicios import crear_estudio

    return crear_estudio(datos, empleado)


@pytest.fixture
def prueba_extra():
    from pruebas.models import Prueba

    return Prueba.objects.create(codigo="TEST-C", nombre="Prueba de test C")
