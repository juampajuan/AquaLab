"""Panel de inicio (SCRUM-67, US4)."""

import datetime
import re
import uuid

import pytest
from django.conf import settings
from django.db import connection
from django.shortcuts import resolve_url
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from clientes.models import Cliente
from estudios.models import Estudio, TipoEstudio
from muestras.models import Muestra, Origen

pytestmark = pytest.mark.django_db

ACCESOS = ("clientes:buscar", "clientes:registrar", "muestras:registrar", "estudios:crear")


@pytest.fixture
def empleado(django_user_model):
    return django_user_model.objects.create_user(
        email="panel@example.com", password="Clave-Panel-Segura-852", first_name="Elena"
    )


@pytest.fixture
def cliente_http(client, empleado):
    client.force_login(empleado)
    return client


@pytest.fixture
def cliente():
    return Cliente.objects.create(
        razon_social="Aguas del Sur S.A.",
        tipo_documento="CUIT",
        numero_documento="20123456786",
        email="contacto@aguassur.com",
    )


@pytest.fixture
def origen(cliente):
    return Origen.objects.create(cliente=cliente, nombre="Pozo N°2")


@pytest.fixture
def crear_muestra(cliente, origen, empleado):
    def crear(numero_pi, fecha_ingreso=None):
        fecha = fecha_ingreso or timezone.localdate()
        return Muestra.objects.create(
            numero_pi=numero_pi,
            nombre=f"Muestra {numero_pi}",
            cliente=cliente,
            origen=origen,
            fecha_muestreo=fecha,
            fecha_ingreso=fecha,
            sitio_extraccion="Canilla",
            registrada_por=empleado,
        )

    return crear


@pytest.fixture
def crear_estudio(empleado):
    tipo = TipoEstudio.objects.create(nombre="Bacteriológico")

    def crear(muestra):
        return Estudio.objects.create(
            muestra=muestra,
            tipo=tipo,
            creado_por=empleado,
            tipo_nombre_snapshot=tipo.nombre,
            tipo_version_snapshot=tipo.version,
            clave_idempotencia=uuid.uuid4(),
        )

    return crear


def panel(cliente_http):
    return cliente_http.get(reverse("inicio")).content.decode()


def indicador(html, nombre):
    encontrado = re.search(rf'data-indicador="{nombre}"[^>]*>.*?data-valor>(\d+)<', html, re.S)
    assert encontrado, f"no se encontró el indicador {nombre}"
    return int(encontrado.group(1))


def filas_de_ultimas(html):
    tabla = re.search(r'data-componente="ultimas-muestras".*?</table>', html, re.S)
    assert tabla, "no se encontró la tabla de últimas muestras"
    return re.findall(r"<tr data-pi=\"(\d+)\">(.*?)</tr>", tabla.group(0), re.S)


# Escenarios 1 y 2: saludo y accesos rápidos


def test_accesos_rapidos_llevan_a_cada_pantalla(cliente_http):
    html = panel(cliente_http)
    accesos = re.search(r'data-componente="accesos".*?</section>', html, re.S).group(0)

    assert "Bienvenido/a a AquaLab" in html
    for nombre in ACCESOS:
        assert f'href="{reverse(nombre)}"' in accesos, nombre


# Escenario 3: muestras sin estudio


def test_muestras_sin_estudio_cuenta_solo_las_que_no_tienen_estudios(
    cliente_http, crear_muestra, crear_estudio
):
    con_estudio = crear_muestra(200001)
    crear_estudio(con_estudio)
    crear_estudio(con_estudio)
    crear_muestra(200002)
    crear_muestra(200003)

    assert indicador(panel(cliente_http), "muestras-sin-estudio") == 2


# Escenario 4: muestras ingresadas hoy


def test_muestras_hoy_cuenta_solo_la_fecha_de_ingreso_de_hoy(cliente_http, crear_muestra):
    hoy = timezone.localdate()
    crear_muestra(200001, hoy)
    crear_muestra(200002, hoy)
    crear_muestra(200003, hoy - datetime.timedelta(days=1))

    assert indicador(panel(cliente_http), "muestras-hoy") == 2


# Escenario 5: estudios pendientes


def test_estudios_pendientes_cuenta_los_estudios_en_ese_estado(
    cliente_http, crear_muestra, crear_estudio
):
    muestra = crear_muestra(200001)
    crear_estudio(muestra)
    crear_estudio(crear_muestra(200002))

    assert indicador(panel(cliente_http), "estudios-pendientes") == 2


# Escenario 6: últimas muestras


def test_tabla_muestra_las_cinco_mas_recientes_con_sus_datos(cliente_http, crear_muestra):
    ayer = timezone.localdate() - datetime.timedelta(days=1)
    for numero_pi in range(200001, 200008):
        crear_muestra(numero_pi, ayer)

    filas = filas_de_ultimas(panel(cliente_http))

    assert [int(pi) for pi, _ in filas] == [200007, 200006, 200005, 200004, 200003]
    contenido = filas[0][1]
    assert "Aguas del Sur S.A." in contenido
    assert "Pozo N°2" in contenido
    assert ayer.strftime("%d/%m/%Y") in contenido
    assert 'data-estado="info">Ingresada' in contenido


# Escenario 7: base sin muestras


def test_sin_muestras_indicadores_en_cero_y_estado_vacio(cliente_http):
    html = panel(cliente_http)

    for nombre in ("muestras-sin-estudio", "muestras-hoy", "estudios-pendientes"):
        assert indicador(html, nombre) == 0
    vacio = re.search(r'data-componente="estado-vacio".*?</div>\s*</div>', html, re.S).group(0)
    assert f'href="{reverse("muestras:registrar")}"' in vacio


# Transversales


def test_inicio_requiere_sesion(client):
    respuesta = client.get(reverse("inicio"))

    assert respuesta.status_code == 302
    assert respuesta.url.startswith(resolve_url(settings.LOGIN_URL))


def test_inicio_conserva_la_huella_de_sesion(cliente_http):
    assert cliente_http.get(reverse("inicio")).context["huella_sesion"]


def test_consultas_no_crecen_con_la_cantidad_de_muestras(cliente_http, crear_muestra):
    crear_muestra(200001)
    with CaptureQueriesContext(connection) as con_una:
        panel(cliente_http)

    for numero_pi in range(200002, 200007):
        crear_muestra(numero_pi)
    with CaptureQueriesContext(connection) as con_seis:
        panel(cliente_http)

    assert len(con_seis) == len(con_una)
