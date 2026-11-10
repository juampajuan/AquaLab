import uuid

import pytest
from django.utils import timezone

# Fixtures de estudios (catalogo, estudio_de, bioquimico…); las de abajo con el mismo nombre ganan.
from estudios.tests.conftest import *  # noqa: F401,F403


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


@pytest.fixture
def administrador_catalogo(django_user_model):
    """Usuario del grupo «Administradores» con el permiso del panel (SCRUM-71/73)."""
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    from usuarios.models import Usuario

    permiso, _ = Permission.objects.get_or_create(
        content_type=ContentType.objects.get_for_model(Usuario),
        codename="administrar_panel",
        defaults={"name": "Puede administrar el panel de AquaLab"},
    )
    grupo, _ = Group.objects.get_or_create(name="Administradores")
    grupo.permissions.add(permiso)
    usuario = django_user_model.objects.create_user(
        email="catalogo@lab.com", password="Clave-Valida-123", first_name="Ana", last_name="Admin"
    )
    usuario.groups.add(grupo)
    return usuario


@pytest.fixture
def cliente_catalogo(client, administrador_catalogo):
    client.force_login(administrador_catalogo)
    return client


@pytest.fixture
def datos_prueba():
    """Datos completos de una prueba para el formulario y el servicio."""

    def armar(**cambios):
        datos = {
            "codigo": "TEST-DIR",
            "nombre": "Prueba directa",
            "tipo_calculo": "DIRECTO",
            "formula": "",
            "unidad_medicion": "mg/l",
            "unidad": "mg/l",
            "limite_min": "",
            "limite_max": "10",
            "norma": "Norma X",
            "limite_deteccion": "0.1",
            "cloacal_limite_min": "",
            "cloacal_limite_max": "",
            "cloacal_norma": "",
            "canal_limite_min": "",
            "canal_limite_max": "",
            "canal_norma": "",
            "observacion": "",
        }
        datos.update(cambios)
        return datos

    return armar
