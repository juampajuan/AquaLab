import pytest
from django.utils import timezone

from estudios.tests.conftest import *  # noqa: F401,F403


@pytest.fixture
def completar():
    """Pasa a Completada las asignaciones de esos códigos (todas si no se indican).

    Atajo para no validar cada prueba (US 6.4): `estado` es editable=False.
    """
    from estudios.models import EstadoPruebaEstudio

    def marcar(estudio, *codigos):
        asignaciones = estudio.pruebas_asignadas.all()
        if codigos:
            asignaciones = asignaciones.filter(prueba__codigo__in=codigos)
        asignaciones.update(estado=EstadoPruebaEstudio.COMPLETADA)

    return marcar


@pytest.fixture
def emitir():
    """Marca el informe del estudio como emitido (US 7.2 todavía no existe)."""
    from estudios.models import EstadoEstudio, Estudio

    def marcar(estudio):
        Estudio.objects.filter(pk=estudio.pk).update(estado=EstadoEstudio.INFORME_GENERADO)

    return marcar


@pytest.fixture
def otra_muestra(empleado):
    """Crea una muestra con su propio cliente, para estudios que se distinguen al buscar."""
    from clientes.models import Cliente
    from muestras.models import Muestra, Origen

    def crear(numero_pi, nombre_cliente, numero_documento, nombre="Otra muestra", **cliente):
        datos_cliente = {
            "nombre": nombre_cliente,
            "tipo_documento": "DNI",
            "numero_documento": numero_documento,
            "email": f"{numero_documento}@ejemplo.com",
            **cliente,
        }
        cliente_obj = Cliente.objects.create(**datos_cliente)
        origen = Origen.objects.create(cliente=cliente_obj, nombre=f"Origen {numero_pi}")
        return Muestra.objects.create(
            numero_pi=numero_pi,
            nombre=nombre,
            cliente=cliente_obj,
            origen=origen,
            fecha_muestreo=timezone.localdate(),
            fecha_ingreso=timezone.localdate(),
            sitio_extraccion="Sitio test",
            registrada_por=empleado,
        )

    return crear


@pytest.fixture
def estudio_para(empleado, catalogo):
    """Como `estudio_de` (estudios/tests/conftest.py), pero en la muestra que se indique."""
    import uuid

    from estudios.models import TipoEstudio
    from estudios.servicios import crear_estudio
    from pruebas.models import Prueba

    nombres = iter(f"Tipo {a}{b}" for a in "ABCDEFGH" for b in "ABCDEFGH")

    def crear(muestra, *codigos):
        # Nombre sin dígitos: buscar por N° de estudio no debe coincidir con el tipo.
        tipo = TipoEstudio.objects.create(nombre=next(nombres))
        tipo.pruebas.set(Prueba.objects.filter(codigo__in=codigos))
        datos = {
            "clave": str(uuid.uuid4()),
            "muestra": muestra.pk,
            "tipo": tipo.pk,
            "version": tipo.version,
        }
        return crear_estudio(datos, empleado)

    return crear
