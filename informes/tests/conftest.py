import pytest
from django.utils import timezone

from estudios.tests.conftest import *  # noqa: F401,F403


@pytest.fixture
def completar():
    """Pasa a Completada las asignaciones de esos códigos (todas si no se indican).

    Atajo para no validar cada prueba (US 6.4): `estado` es editable=False. No crea la
    `Validacion`, así que deja pruebas Completadas sin validación vigente, algo que en la app
    real no ocurre; para el flujo completo usar `validar()` de `estudios/tests/utiles.py`.
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


@pytest.fixture
def emitir_de(estudio_para, completar, bioquimico):
    """Emite el informe de un estudio nuevo con esos códigos en la muestra dada (US 7.3)."""
    from informes.servicios import emitir_informe

    def crear(muestra, *codigos):
        estudio = estudio_para(muestra, *(codigos or ("PH",)))
        completar(estudio)
        return emitir_informe(estudio.pk, bioquimico)

    return crear


@pytest.fixture
def tres_informes(otra_muestra, emitir_de):
    """INF-000001 y INF-000003 de «Aguas del Sur SA» (CUIT); INF-000002 de «José Núñez» (DNI)."""
    sur = otra_muestra(
        200101, "", "30712345678", tipo_documento="CUIT", razon_social="Aguas del Sur SA"
    )
    jose = otra_muestra(200102, "José Núñez", "28444555")
    sur_2 = otra_muestra(
        200103, "", "30712345679", tipo_documento="CUIT", razon_social="Aguas del Sur SA"
    )
    return emitir_de(sur), emitir_de(jose), emitir_de(sur_2)


@pytest.fixture
def con_fecha():
    """Cambia la fecha de emisión (hora de Buenos Aires) sin pasar por save()."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from informes.models import Informe

    def cambiar(informe, anio, mes, dia, hora=12, minuto=0):
        fecha = datetime(
            anio, mes, dia, hora, minuto, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires")
        )
        Informe.objects.filter(pk=informe.pk).update(fecha_emision=fecha)
        informe.refresh_from_db()
        return informe

    return cambiar


@pytest.fixture
def cliente_comun(django_user_model):
    """Cliente HTTP de un empleado sin `informes.emitir_informes` (SCRUM-79).

    `cliente_http` no sirve para esto: su usuario es el mismo `empleado` que `bioquimico` suma al
    grupo «Bioquímicos».
    """
    from django.test import Client

    usuario = django_user_model.objects.create_user(
        email="comun-envios@ejemplo.com", password="Clave-Valida-123", is_active=True
    )
    cliente = Client()
    cliente.force_login(usuario)
    return cliente


@pytest.fixture
def evaluadas(empleado, catalogo, cliente_a):
    """Validaciones vigentes con la evaluación elegida, para la sección «Calidad» (US 8.4).

    `crear({"CL-": (2, 10)}, sin_limite={"COND": 3}, origen=..., tipo_vertido=..., momento=...)`
    deja 10 resultados evaluados de Cloruro (2 fuera de norma) y 3 de Conductividad sin límite
    comparable. Arma los estudios y las validaciones directo en la base, sin cargar ni validar:
    la sección solo lee la evaluación guardada. Para el flujo real usar `estudio_en_origen`.
    Con `momento`, las validaciones nacen en esa fecha (`demo.reloj`). Devuelve los estudios.
    """
    import itertools
    import uuid

    from estudios import demo
    from estudios.models import Estudio, OrigenLimites, PruebaEstudio, TipoEstudio, Validacion
    from muestras.models import Muestra, Origen, TipoVertido
    from pruebas.limites import Evaluacion

    numeros = itertools.count(400001)
    origen_por_defecto = []

    def crear(
        por_codigo, *, sin_limite=None, origen=None, tipo_vertido=TipoVertido.AGUA, momento=None
    ):
        if origen is None:
            if not origen_por_defecto:
                origen_por_defecto.append(
                    Origen.objects.create(cliente=cliente_a, nombre="Origen de calidad")
                )
            origen = origen_por_defecto[0]
        planes = {}  # código → evaluaciones, una por estudio
        for codigo, (fuera, evaluados) in por_codigo.items():
            planes[codigo] = [Evaluacion.FUERA_DE_NORMA] * fuera + [Evaluacion.CUMPLE] * (
                evaluados - fuera
            )
        for codigo, cantidad in (sin_limite or {}).items():
            planes.setdefault(codigo, []).extend([Evaluacion.SIN_LIMITE] * cantidad)
        hoy = timezone.localdate(momento) if momento else timezone.localdate()
        numero = next(numeros)
        muestra = Muestra.objects.create(
            numero_pi=numero,
            nombre=f"Muestra {numero}",
            cliente=origen.cliente,
            origen=origen,
            fecha_muestreo=hoy,
            fecha_ingreso=hoy,
            sitio_extraccion="Sitio test",
            tipo_vertido=tipo_vertido,
            registrada_por=empleado,
        )
        tipo = TipoEstudio.objects.create(nombre=f"Tipo de calidad {uuid.uuid4()}")
        estudios = []
        with demo.reloj(momento or timezone.now()):
            for i in range(max((len(e) for e in planes.values()), default=0)):
                estudio = Estudio.objects.create(
                    muestra=muestra,
                    tipo=tipo,
                    creado_por=empleado,
                    tipo_nombre_snapshot=tipo.nombre,
                    tipo_version_snapshot=tipo.version,
                    clave_idempotencia=uuid.uuid4(),
                )
                for codigo, plan in planes.items():
                    if i < len(plan):
                        asignacion = PruebaEstudio.objects.create(
                            estudio=estudio, prueba=catalogo[codigo]
                        )
                        Validacion.objects.create(
                            asignacion=asignacion,
                            validada_por=empleado,
                            origen_limites=OrigenLimites.GENERAL,
                            evaluacion=plan[i],
                        )
                estudios.append(estudio)
        return estudios

    return crear
