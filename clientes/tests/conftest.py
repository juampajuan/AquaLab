import uuid

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


@pytest.fixture
def muestra_de(empleado):
    """Fábrica de muestras para el historial (US 3.3): `muestra_de(cliente, fecha, numero_pi)`."""
    from muestras.models import Muestra, Origen

    def crear(cliente, fecha_ingreso, numero_pi, origen="Pozo 1"):
        origen_obj, _ = Origen.objects.get_or_create(cliente=cliente, nombre=origen)
        return Muestra.objects.create(
            numero_pi=numero_pi,
            nombre=f"Muestra {numero_pi}",
            cliente=cliente,
            origen=origen_obj,
            fecha_muestreo=fecha_ingreso,
            fecha_ingreso=fecha_ingreso,
            sitio_extraccion="Sitio test",
            registrada_por=empleado,
        )

    return crear


@pytest.fixture
def estudio_en(empleado):
    """Fábrica de estudios en un estado dado, con informe opcional (US 3.3).

    `estado` es `editable=False`: se fija con `update()`. Con `con_informe=True` el estudio queda en
    «Informe generado» y se crea su `Informe` (número correlativo dentro del test).
    """
    from estudios.models import EstadoEstudio, Estudio, TipoEstudio
    from informes.models import Informe

    def crear(
        muestra, estado=EstadoEstudio.PENDIENTE_ANALISIS, tipo="Agua de red", con_informe=False
    ):
        tipo_obj, _ = TipoEstudio.objects.get_or_create(nombre=tipo)
        estudio = Estudio.objects.create(
            muestra=muestra,
            tipo=tipo_obj,
            creado_por=empleado,
            tipo_nombre_snapshot=tipo,
            tipo_version_snapshot=1,
            clave_idempotencia=uuid.uuid4(),
        )
        if con_informe:
            estado = EstadoEstudio.INFORME_GENERADO
            Informe.objects.create(
                numero=Informe.objects.count() + 1,
                estudio=estudio,
                emitido_por=empleado,
                contenido={},
            )
        Estudio.objects.filter(pk=estudio.pk).update(estado=estado)
        return Estudio.objects.get(pk=estudio.pk)

    return crear
