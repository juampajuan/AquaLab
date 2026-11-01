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


@pytest.fixture
def asignacion(estudio):
    return estudio.pruebas_asignadas.get(prueba__codigo="TEST-A")


@pytest.fixture
def pruebas_medicion():
    from pruebas.models import Prueba, TipoCalculo

    return {
        p.codigo: p
        for p in [
            Prueba.objects.create(codigo="TEST-PH", nombre="pH de test", unidad_medicion="UpH"),
            Prueba.objects.create(
                codigo="TEST-VOL", nombre="Volumen de test", unidad_medicion="mL"
            ),
            Prueba.objects.create(codigo="TEST-SIN", nombre="Sin unidad de test"),
            Prueba.objects.create(
                codigo="TEST-CALC",
                nombre="Calculada de test",
                tipo_calculo=TipoCalculo.FORMULA,
                formula="{TEST-PH} * 2",
                es_calculada=True,
            ),
        ]
    }


@pytest.fixture
def estudio_mediciones(muestra, empleado, pruebas_medicion):
    from estudios.models import TipoEstudio
    from estudios.servicios import crear_estudio

    tipo = TipoEstudio.objects.create(nombre="Tipo mediciones de test")
    tipo.pruebas.set(pruebas_medicion.values())
    datos = {
        "clave": str(uuid.uuid4()),
        "muestra": muestra.pk,
        "tipo": tipo.pk,
        "version": tipo.version,
    }
    return crear_estudio(datos, empleado)


@pytest.fixture
def asignaciones_medicion(estudio_mediciones):
    return {
        a.prueba.codigo: a for a in estudio_mediciones.pruebas_asignadas.select_related("prueba")
    }


@pytest.fixture
def catalogo():
    import io

    from django.core.management import call_command

    from pruebas.models import Prueba

    call_command("importar_catalogo_pruebas", stdout=io.StringIO())
    return {p.codigo: p for p in Prueba.objects.all()}


@pytest.fixture
def pruebas_division():
    from pruebas.models import Prueba, TipoCalculo

    return [
        Prueba.objects.create(codigo="DIV-A", nombre="Dividendo", unidad="u", unidad_medicion="u"),
        Prueba.objects.create(codigo="DIV-B", nombre="Divisor", unidad="u", unidad_medicion="u"),
        Prueba.objects.create(
            codigo="DIV",
            nombre="Cociente",
            unidad="u",
            tipo_calculo=TipoCalculo.FORMULA,
            formula="{DIV-A}/{DIV-B}",
            es_calculada=True,
        ),
    ]


@pytest.fixture
def estudio_de(muestra, empleado, catalogo):
    from estudios.models import TipoEstudio
    from estudios.servicios import crear_estudio
    from pruebas.models import Prueba

    def crear(*codigos):
        tipo = TipoEstudio.objects.create(nombre=f"Tipo de cálculo {uuid.uuid4()}")
        tipo.pruebas.set(Prueba.objects.filter(codigo__in=codigos))
        datos = {
            "clave": str(uuid.uuid4()),
            "muestra": muestra.pk,
            "tipo": tipo.pk,
            "version": tipo.version,
        }
        return crear_estudio(datos, empleado)

    return crear
