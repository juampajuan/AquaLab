"""Filtros de «Buscar estudio» por estado y fecha de creación (SCRUM-74)."""

import re
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.conf import settings
from django.urls import reverse

from estudios.models import EstadoEstudio, Estudio
from estudios.servicios import crear_estudio

pytestmark = pytest.mark.django_db

ZONA = ZoneInfo(settings.TIME_ZONE)


def local(anio, mes, dia, hora=12, minuto=0, segundo=0):
    """Fecha y hora en la zona del laboratorio."""
    return datetime(anio, mes, dia, hora, minuto, segundo, tzinfo=ZONA)


def estudio_creado(muestra, tipo, usuario, estado=EstadoEstudio.PENDIENTE_ANALISIS, creado=None):
    """Estudio creado con el servicio real; el estado y la fecha se fijan después (datos de test:
    `estado` no es editable y `fecha_creacion` es `auto_now_add`)."""
    estudio = crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra.pk,
            "tipo": tipo.pk,
            "version": tipo.version,
        },
        usuario,
    )
    cambios = {"estado": estado}
    if creado is not None:
        cambios["fecha_creacion"] = creado
    Estudio.objects.filter(pk=estudio.pk).update(**cambios)
    estudio.refresh_from_db()
    return estudio


def buscar(cliente_http, **parametros):
    return cliente_http.get(reverse("estudios:buscar"), parametros)


def listados(resp):
    return list(resp.context["page_obj"].object_list)


@pytest.fixture
def un_estudio_por_estado(muestra, tipo, empleado):
    return {
        estado: estudio_creado(muestra, tipo, empleado, estado=estado)
        for estado in EstadoEstudio.values
    }


# --- US1: filtrar por estado -------------------------------------------------------------------


def test_muestra_los_filtros(cliente_http, un_estudio_por_estado):
    html = buscar(cliente_http).content.decode()

    select = re.search(r'<select name="estado"[^>]*>(.*?)</select>', html, re.S)
    assert select
    opciones = re.findall(r"<option[^>]*>([^<]*)</option>", select.group(1))
    assert opciones == ["Todos", *(texto for _, texto in EstadoEstudio.choices)]
    assert re.search(r'<option value=""[^>]*selected', select.group(1))
    for nombre, etiqueta in (("desde", "Desde"), ("hasta", "Hasta")):
        assert re.search(rf'<input type="date" name="{nombre}"', html)
        assert re.search(rf'<label for="id_{nombre}"[^>]*>\s*{etiqueta}\s*</label>', html)
    assert re.search(r'<label for="id_estado"[^>]*>\s*Estado\s*</label>', html)


@pytest.mark.parametrize("estado", EstadoEstudio.values)
def test_filtra_por_estado(cliente_http, un_estudio_por_estado, estado):
    resp = buscar(cliente_http, estado=estado)

    assert listados(resp) == [un_estudio_por_estado[estado]]
    assert "1 estudio encontrado" in resp.content.decode()


def test_estado_todos_no_restringe(cliente_http, un_estudio_por_estado):
    resp = buscar(cliente_http, estado="")

    assert set(listados(resp)) == set(un_estudio_por_estado.values())


@pytest.mark.parametrize(
    ("parametros", "campo", "error"),
    [
        ({"estado": "otro"}, "estado", "Elegí un estado de la lista."),
        ({"desde": "31/02/2026"}, "desde", "Ingresá una fecha válida (dd/mm/aaaa)."),
        ({"hasta": "no-es-fecha"}, "hasta", "Ingresá una fecha válida (dd/mm/aaaa)."),
        (
            {"desde": "2026-11-10", "hasta": "2026-11-01"},
            "desde",
            "La fecha desde no puede ser posterior a la fecha hasta.",
        ),
        ({"estado": "en_proceso", "desde": "x"}, "desde", "Ingresá una fecha válida (dd/mm/aaaa)."),
    ],
)
def test_filtros_invalidos(cliente_http, un_estudio_por_estado, parametros, campo, error):
    resp = buscar(cliente_http, **parametros)

    assert resp.status_code == 200
    html = resp.content.decode()
    assert error in html
    assert re.search(rf'<(input|select)[^>]*name="{campo}"[^>]*class="[^"]*is-invalid', html) or (
        re.search(rf'<(input|select)[^>]*class="[^"]*is-invalid[^"]*"[^>]*name="{campo}"', html)
    )
    for nombre, valor in parametros.items():
        if nombre != "estado":
            assert f'value="{valor}"' in html
    # Con un valor inválido no se filtra: se ve el listado completo.
    assert resp.context["page_obj"].paginator.count == len(EstadoEstudio.values)


# --- US2: filtrar por fecha de creación --------------------------------------------------------


@pytest.fixture
def estudios_por_fecha(muestra, tipo, empleado):
    return {
        dia: estudio_creado(muestra, tipo, empleado, creado=local(2026, 11, dia))
        for dia in (1, 5, 10)
    }


@pytest.mark.parametrize(
    ("parametros", "dias"),
    [
        ({"desde": "2026-11-05", "hasta": "2026-11-10"}, {5, 10}),
        ({"desde": "2026-11-05"}, {5, 10}),
        ({"hasta": "2026-11-05"}, {1, 5}),
        ({"desde": "2026-11-05", "hasta": "2026-11-05"}, {5}),
        ({"desde": "05/11/2026", "hasta": "10/11/2026"}, {5, 10}),
    ],
)
def test_filtro_fechas(cliente_http, estudios_por_fecha, parametros, dias):
    resp = buscar(cliente_http, **parametros)

    assert set(listados(resp)) == {estudios_por_fecha[d] for d in dias}


def test_bordes_del_dia_en_zona_del_laboratorio(cliente_http, muestra, tipo, empleado):
    # 23:59:59 local del 05/11 es 02:59:59 UTC del 06/11: el día se cuenta en la zona del
    # laboratorio, no en UTC.
    adentro = [
        estudio_creado(muestra, tipo, empleado, creado=local(2026, 11, 5, 0, 0, 0)),
        estudio_creado(muestra, tipo, empleado, creado=local(2026, 11, 5, 23, 59, 59)),
    ]
    estudio_creado(muestra, tipo, empleado, creado=local(2026, 11, 4, 23, 59, 59))
    estudio_creado(muestra, tipo, empleado, creado=local(2026, 11, 6, 0, 0, 0))

    resp = buscar(cliente_http, desde="2026-11-05", hasta="2026-11-05")

    assert set(listados(resp)) == set(adentro)


def test_filtro_estado_fechas_vacio(un_estudio_por_estado):
    from estudios.busqueda import filtro_estado_fechas

    assert Estudio.objects.filter(filtro_estado_fechas()).count() == len(EstadoEstudio.values)


def test_ayuda_en_fechas(cliente_http):
    html = buscar(cliente_http).content.decode()

    for nombre in ("desde", "hasta"):
        ayuda = f"id_{nombre}_helptext"
        assert re.search(
            rf'role="tooltip" id="{ayuda}"[^>]*>\s*Fecha en que se creó el estudio\. '
            r"El día indicado se incluye\.",
            html,
        )
        control = re.search(rf'<input type="date" name="{nombre}"[^>]*>', html).group()
        assert re.search(rf'aria-describedby="[^"]*{ayuda}', control)


# --- US3: combinar, paginar y limpiar ----------------------------------------------------------


@pytest.fixture
def otra_muestra(empleado):
    from clientes.models import Cliente
    from muestras.models import Muestra, Origen

    cliente = Cliente.objects.create(
        razon_social="Lácteos del Sur S.A.",
        tipo_documento="CUIT",
        numero_documento="20123456786",
        email="lacteos@ejemplo.com",
    )
    origen = Origen.objects.create(cliente=cliente, nombre="Pozo 2")
    return Muestra.objects.create(
        numero_pi=200002,
        nombre="Pozo 2 noviembre",
        cliente=cliente,
        origen=origen,
        fecha_muestreo=local(2026, 11, 5).date(),
        fecha_ingreso=local(2026, 11, 5).date(),
        sitio_extraccion="Canilla",
        registrada_por=empleado,
    )


def test_filtros_combinados_con_texto(cliente_http, muestra, otra_muestra, tipo, empleado):
    en_proceso = EstadoEstudio.EN_PROCESO
    buscado = estudio_creado(otra_muestra, tipo, empleado, en_proceso, local(2026, 11, 5))
    # Cada uno falla un solo criterio.
    estudio_creado(muestra, tipo, empleado, en_proceso, local(2026, 11, 5))  # otro cliente
    estudio_creado(otra_muestra, tipo, empleado, EstadoEstudio.FINALIZADO, local(2026, 11, 5))
    estudio_creado(otra_muestra, tipo, empleado, en_proceso, local(2026, 10, 20))  # fuera de rango

    resp = buscar(
        cliente_http, q="Lácteos", estado="en_proceso", desde="2026-11-01", hasta="2026-11-30"
    )

    assert listados(resp) == [buscado]


def test_paginacion_conserva_filtros(cliente_http, muestra, tipo, empleado):
    for _ in range(21):
        estudio_creado(muestra, tipo, empleado, EstadoEstudio.EN_PROCESO, local(2026, 11, 5))
    for _ in range(2):
        estudio_creado(muestra, tipo, empleado, creado=local(2026, 11, 5))
    filtros = {
        "q": "Muestra test",
        "estado": "en_proceso",
        "desde": "2026-11-01",
        "hasta": "2026-11-30",
    }

    html = buscar(cliente_http, **filtros).content.decode()
    siguiente = (
        re.search(r'href="\?([^"]*)"[^>]*>\s*Siguiente', html).group(1).replace("&amp;", "&")
    )
    for parte in ("q=Muestra+test", "estado=en_proceso", "desde=2026-11-01", "hasta=2026-11-30"):
        assert parte in siguiente
    assert siguiente.count("page=") == 1 and "page=2" in siguiente

    resp = buscar(cliente_http, **filtros, page="2")
    assert len(listados(resp)) == 1
    pagina = resp.content.decode()
    assert 'value="Muestra test"' in pagina
    assert re.search(r'<option value="en_proceso"[^>]*selected', pagina)
    assert 'value="2026-11-01"' in pagina and 'value="2026-11-30"' in pagina

    # Página inexistente: se muestra la última.
    resp = buscar(cliente_http, **filtros, page="99")
    assert resp.context["page_obj"].number == 2


@pytest.mark.parametrize(
    ("parametros", "ofrece"),
    [
        ({"q": "Muestra"}, True),
        ({"estado": "en_proceso"}, True),
        ({"desde": "2026-11-01"}, True),
        ({"desde": "x"}, True),
        ({}, False),
        ({"q": "  "}, False),
    ],
)
def test_limpiar_filtros(cliente_http, un_estudio_por_estado, parametros, ofrece):
    html = buscar(cliente_http, **parametros).content.decode()

    enlace = re.search(
        rf'<a href="{re.escape(reverse("estudios:buscar"))}"[^>]*>(?:(?!</a>).)*Limpiar filtros',
        html,
        re.S,
    )
    assert bool(enlace) is ofrece
    assert "Ver todos" not in html


def test_sin_coincidencias_con_filtros(cliente_http, muestra, tipo, empleado):
    html = buscar(cliente_http).content.decode()
    assert "Aún no hay estudios registrados." in html

    estudio_creado(muestra, tipo, empleado, creado=local(2026, 11, 5))

    html = buscar(cliente_http, desde="2026-12-01").content.decode()
    assert "Ningún estudio coincide con la búsqueda y los filtros." in html
    assert "Aún no hay estudios registrados." not in html
    assert re.search(r"Ningún estudio coincide(?:(?!</section>).)*Limpiar filtros", html, re.S)

    html = buscar(cliente_http, q="zzzz").content.decode()
    assert "No se encontraron estudios para «zzzz»." in html
    assert "Ningún estudio coincide con la búsqueda y los filtros." not in html


def test_consultas_no_dependen_de_los_filtros(cliente_http, muestra, tipo, empleado):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    for _ in range(25):
        estudio_creado(muestra, tipo, empleado, EstadoEstudio.EN_PROCESO, local(2026, 11, 5))

    with CaptureQueriesContext(connection) as sin_filtros:
        buscar(cliente_http)
    with CaptureQueriesContext(connection) as con_filtros:
        buscar(
            cliente_http,
            q="Muestra test",
            estado="en_proceso",
            desde="2026-11-01",
            hasta="2026-11-30",
        )

    assert len(con_filtros) == len(sin_filtros)


@pytest.mark.parametrize(
    "datos",
    [{"desde": "2026-11-10", "hasta": "2026-11-01"}, {"estado": "otro"}, {"hasta": "x"}],
)
def test_formulario_comparte_reglas_con_historial(datos):
    from clientes.forms import HistorialClienteForm
    from estudios.forms import FiltrarEstudiosForm, FiltrosEstudioForm

    assert issubclass(HistorialClienteForm, FiltrosEstudioForm)
    assert issubclass(FiltrarEstudiosForm, FiltrosEstudioForm)
    busqueda, historial = FiltrarEstudiosForm(datos), HistorialClienteForm(datos)
    assert not busqueda.is_valid() and not historial.is_valid()
    assert busqueda.errors == historial.errors
