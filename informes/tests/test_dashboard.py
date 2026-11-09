"""Tests de la pantalla del dashboard (US 8.3): vista, template, menú y permisos."""

import datetime as dt
import io
import re

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from estudios import demo
from estudios.models import Estudio, Medicion, Validacion
from informes.models import Informe
from muestras.models import Muestra

pytestmark = pytest.mark.django_db

URL = reverse("informes:dashboard")


def html_de(respuesta):
    return respuesta.content.decode()


def dia_2():
    hoy = timezone.localtime()
    ahora = hoy.replace(day=2, hour=12, minute=0, second=0, microsecond=0)
    if ahora > hoy:
        ahora = (ahora.replace(day=1) - dt.timedelta(days=1)).replace(day=2)
    return ahora


@pytest.fixture
def con_demo(catalogo):
    demo.cargar_demo(io.StringIO(), ahora=dia_2())


def usuario_con(django_user_model, email, *grupos, **extra):
    usuario = django_user_model.objects.create_user(
        email=email, password="Clave-Valida-123", is_active=True, **extra
    )
    for nombre in grupos:
        usuario.groups.add(Group.objects.get_or_create(name=nombre)[0])
    cliente = Client()
    cliente.force_login(usuario)
    return cliente


# --- US4: acceso -------------------------------------------------------------------------------


def test_acceso_sin_sesion():
    respuesta = Client().get(URL)
    assert respuesta.status_code == 302
    assert respuesta["Location"].startswith(reverse("usuarios:login"))


@pytest.mark.parametrize(
    ("grupos", "superusuario", "estado"),
    [
        ((), False, 403),
        (("Bioquímicos",), False, 200),
        (("Administradores",), False, 200),
        ((), True, 200),  # Django: el superusuario tiene todos los permisos.
    ],
)
def test_acceso(django_user_model, grupos, superusuario, estado):
    cliente = usuario_con(
        django_user_model, "acceso@ejemplo.com", *grupos, is_superuser=superusuario
    )
    respuesta = cliente.get(URL)
    assert respuesta.status_code == estado
    menu = html_de(cliente.get(reverse("inicio")))
    assert (f'href="{URL}"' in menu) == (estado == 200)
    if estado == 200:
        html = html_de(respuesta)
        assert f'href="{URL}" ' in html
        assert 'aria-current="page"' in html.split(f'href="{URL}"')[1].split(">")[0]
        inicio = menu.index(f'href="{reverse("inicio")}"')
        assert (
            inicio
            < menu.index(f'href="{URL}"')
            < menu.index(f'href="{reverse("clientes:buscar")}"')
        )


def test_permiso_en_grupos():
    from importlib import import_module

    from django.apps import apps as registro

    migracion = import_module("informes.migrations.0004_permiso_dashboard")
    Group.objects.filter(name__in=("Bioquímicos", "Administradores")).delete()
    migracion.asignar_permiso(registro, None)
    for nombre in ("Bioquímicos", "Administradores"):
        grupo = Group.objects.get(name=nombre)
        assert grupo.permissions.filter(codename="ver_dashboard").exists()


# --- US1: período e indicadores ----------------------------------------------------------------


def test_selector_de_periodo(cliente_bioquimico):
    for parametro in ("", "?periodo=xyz"):
        html = html_de(cliente_bioquimico.get(URL + parametro))
        assert re.search(r'<option value="este_mes" selected', html)
    html = html_de(cliente_bioquimico.get(URL + "?periodo=ultimos_6"))
    assert re.search(r'<option value="ultimos_6" selected', html)
    for etiqueta in ("Este mes", "Mes anterior", "Últimos 3 meses", "Últimos 6 meses"):
        assert etiqueta in html
    assert "comparado con" in html


def test_indicadores_en_pantalla(cliente_bioquimico, con_demo):
    html = html_de(cliente_bioquimico.get(URL + "?periodo=ultimos_6"))
    for nombre, titulo in (
        ("muestras", "Muestras ingresadas"),
        ("estudios", "Estudios creados"),
        ("informes", "Informes emitidos"),
        ("respuesta", "Tiempo de respuesta"),
    ):
        assert f'data-indicador="{nombre}"' in html
        assert titulo in html
    assert re.search(r'data-tono="(exito|peligro|neutro)"', html)
    assert "sin datos previos" in html  # la demo no tiene datos 6 meses antes
    assert "Estudios por estado" in html
    for estado in ("Pendiente de análisis", "En proceso", "Finalizado", "Informe generado"):
        assert estado in html


# --- US2: gráficos -----------------------------------------------------------------------------


def test_graficos_y_tablas(cliente_bioquimico, con_demo):
    html = html_de(cliente_bioquimico.get(URL))
    assert 'id="grafico-respuesta"' in html
    assert 'id="grafico-actividad"' in html
    assert html.count('role="img"') >= 2
    assert 'id="datos-dashboard"' in html
    assert "/static/vendor/chart.umd.min.js" in html
    assert "/static/informes/dashboard.js" in html
    assert not re.search(r'src="https?://', html)
    tabla_meses = html.split('data-tabla="respuesta"')[1].split("</table>")[0]
    tabla_semanas = html.split('data-tabla="actividad"')[1].split("</table>")[0]
    assert tabla_meses.count("<tr") == 7  # encabezado + 6 meses
    assert tabla_semanas.count("<tr") == 13  # encabezado + 12 semanas


def test_sin_informes_en_el_periodo(cliente_bioquimico):
    html = html_de(cliente_bioquimico.get(URL))
    assert "Sin informes en el período" in html


# --- US3: alertas ------------------------------------------------------------------------------


def test_alertas_en_pantalla(cliente_bioquimico, con_demo):
    html = html_de(cliente_bioquimico.get(URL))
    sin_avanzar = html.split('data-alerta="sin_avanzar"')[1].split('data-alerta="finalizados"')[0]
    finalizados = html.split('data-alerta="finalizados"')[1]
    assert "Estudios sin avanzar" in html
    assert "Finalizados sin informe" in html
    assert "Ver estudio" in sin_avanzar
    for estudio in Estudio.objects.filter(muestra__origen__nombre="Pozo domiciliario"):
        if estudio.estado == "en_proceso":
            assert reverse("estudios:detalle", args=[estudio.pk]) in sin_avanzar
    escuela = Estudio.objects.get(muestra__origen__nombre="Escuela N° 12", estado="finalizado")
    assert reverse("estudios:detalle", args=[escuela.pk]) in finalizados


def test_alertas_vacias(cliente_bioquimico):
    html = html_de(cliente_bioquimico.get(URL))
    assert html.count("No hay estudios en esta situación.") == 2


# --- Polish: base vacía, solo lectura, consultas ----------------------------------------------


def test_base_vacia(cliente_bioquimico):
    respuesta = cliente_bioquimico.get(URL)
    assert respuesta.status_code == 200
    html = html_de(respuesta)
    assert "Sin informes en el período" in html
    assert "—" in html


def test_solo_lectura(cliente_bioquimico, con_demo):
    modelos = (Muestra, Estudio, Medicion, Validacion, Informe)
    antes = [m.objects.count() for m in modelos]
    cliente_bioquimico.get(URL + "?periodo=ultimos_3")
    assert [m.objects.count() for m in modelos] == antes


def test_cantidad_de_consultas(cliente_bioquimico, con_demo, django_assert_max_num_queries):
    with django_assert_max_num_queries(25):
        assert cliente_bioquimico.get(URL).status_code == 200
