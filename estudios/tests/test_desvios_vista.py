"""Pantallas de los desvíos (US 8.2): detalle del estudio, dashboard y lista de pendientes."""

import datetime as dt
import html as html_lib
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from estudios import desvios
from estudios.demo import reloj
from estudios.models import Validacion
from estudios.tests.utiles import asignacion_de
from muestras.models import Origen

pytestmark = pytest.mark.django_db

DIA = dt.date(2026, 3, 1)


def dia(n):
    return DIA + dt.timedelta(days=n)


def html_de(respuesta):
    return html_lib.unescape(respuesta.content.decode())


def fila(html, codigo):
    """La fila `<tr>` de la tabla de pruebas del detalle cuyo código es `codigo`."""
    posicion = html.index(f">{codigo}</td>")
    return html[html.rindex("<tr", 0, posicion) : html.index("</tr>", posicion)]


def usuario(django_user_model, email, *grupos):
    creado = django_user_model.objects.create_user(
        email=email, password="Clave-Valida-123", is_active=True
    )
    for nombre in grupos:
        creado.groups.add(Group.objects.get(name=nombre))
    cliente = Client()
    cliente.force_login(creado)
    return cliente


@pytest.fixture
def origen(cliente_a):
    return Origen.objects.create(cliente=cliente_a, nombre="Pozo de desvíos")


@pytest.fixture
def historia_cloruro(origen, estudio_en_origen):
    """Cloruro validado 100, 110 y 120 mg/l los días 0, 1 y 2."""
    for n, valor in enumerate(["10", "11", "12"]):
        estudio_en_origen(origen, dia(n), 300401 + n, {"CL-": valor, "PH": "7.0"})


@pytest.fixture
def con_desvio(origen, historia_cloruro, estudio_en_origen):
    """Estudio sin validar con Cloruro 160 mg/l (desvío) y pH 7,1 (sin desvío)."""
    return estudio_en_origen(origen, dia(3), 300410, {"CL-": "16", "PH": "7.1"}, validar_todo=False)


# --- Detalle del estudio (FR-005) ------------------------------------------------------------


def test_marca_en_detalle(con_desvio, cliente_bioquimico, django_user_model):
    url = reverse("estudios:detalle", args=[con_desvio.pk])
    html = html_de(cliente_bioquimico.get(url))
    cloruro = fila(html, "CL-")
    assert 'data-desvio="pendiente"' in cloruro
    assert "Desvío" in cloruro and "<svg" in cloruro.split("data-desvio")[1]
    assert "Observado 160 mg/l" in cloruro
    assert "Mediana de los últimos 3: 110 mg/l" in cloruro
    assert "▲ +50 mg/l (+45,5 %)" in cloruro
    enlace = f"{reverse('estudios:comparacion')}?estudio={con_desvio.pk}&pruebas=CL-&elegir=1"
    assert enlace in cloruro
    assert "data-desvio" not in fila(html, "PH")
    assert "más de un 30 % respecto de la mediana de los últimos 3" in cloruro

    tecnico = usuario(django_user_model, "tecnico-desvios@ejemplo.com")
    sin_permiso = fila(html_de(tecnico.get(url)), "CL-")
    assert "Observado 160 mg/l" in sin_permiso
    assert "Comparación histórica" not in sin_permiso


def test_revisado_en_detalle(con_desvio, bioquimico, cliente_bioquimico):
    from estudios.tests.utiles import validar

    validar(con_desvio, bioquimico, "CL-")
    cl = asignacion_de(con_desvio, "CL-")
    Validacion.objects.filter(asignacion=cl, anulada=False).update(
        observacion="Repetida", desvio_referencia=Decimal(110), desvio_umbral=Decimal(30)
    )
    validacion = Validacion.objects.get(asignacion=cl, anulada=False)

    html = html_de(cliente_bioquimico.get(reverse("estudios:detalle", args=[con_desvio.pk])))
    cloruro = fila(html, "CL-")
    assert 'data-desvio="revisado"' in cloruro and "Desvío revisado" in cloruro
    fecha = timezone.localtime(validacion.fecha_validacion).strftime("%d/%m/%Y %H:%M")
    assert f"el {fecha} – Repetida" in cloruro
    assert "mediana 110 mg/l, umbral 30 %" in cloruro
    assert "Mediana histórica: 110 mg/l" in cloruro


def test_validado_sin_desvio_sin_marca(con_desvio, bioquimico, cliente_bioquimico):
    from estudios.tests.utiles import validar

    validar(con_desvio, bioquimico, "PH")
    html = html_de(cliente_bioquimico.get(reverse("estudios:detalle", args=[con_desvio.pk])))
    assert "data-desvio" not in fila(html, "PH")


# --- Dashboard y lista (FR-006) --------------------------------------------------------------


def pendientes_en(origen, estudio_en_origen, cantidad, desde=300500):
    """`cantidad` estudios sin validar con Cloruro en desvío (uno por muestra)."""
    return [
        estudio_en_origen(origen, dia(10 + n), desde + n, {"CL-": "16"}, validar_todo=False)
        for n in range(cantidad)
    ]


def test_dashboard_contador_y_diez(origen, historia_cloruro, estudio_en_origen, cliente_bioquimico):
    estudios = pendientes_en(origen, estudio_en_origen, 12)
    html = html_de(cliente_bioquimico.get(reverse("informes:dashboard")))
    seccion = html[html.index('aria-labelledby="titulo-desvios"') :]
    seccion = seccion[: seccion.index("</section>")]
    assert "12 pendientes" in seccion
    assert seccion.count("data-desvio-fila") == 10
    assert reverse("estudios:desvios") in seccion and "Ver todos" in seccion
    # Los más recientes primero: el último cargado encabeza.
    primero = seccion.index("data-desvio-fila")
    assert str(estudios[-1].muestra.numero_pi) in seccion[primero : primero + 600]


def test_dashboard_sin_ver_todos_con_pocos(
    origen, historia_cloruro, estudio_en_origen, cliente_bioquimico
):
    pendientes_en(origen, estudio_en_origen, 2)
    html = html_de(cliente_bioquimico.get(reverse("informes:dashboard")))
    seccion = html[html.index('aria-labelledby="titulo-desvios"') :]
    seccion = seccion[: seccion.index("</section>")]
    assert "2 pendientes" in seccion and "Ver todos" not in seccion


def test_dashboard_sin_desvios(cliente_bioquimico):
    html = html_de(cliente_bioquimico.get(reverse("informes:dashboard")))
    assert "Desvíos sin revisar" in html
    assert "No hay desvíos sin revisar" in html


def test_dashboard_no_depende_del_periodo(
    origen, historia_cloruro, estudio_en_origen, cliente_bioquimico
):
    with reloj(timezone.now() - dt.timedelta(days=90)):
        estudio_en_origen(origen, dia(10), 300500, {"CL-": "16"}, validar_todo=False)
    for periodo in ("este_mes", "6_meses"):
        html = html_de(cliente_bioquimico.get(reverse("informes:dashboard"), {"periodo": periodo}))
        assert "1 pendiente" in html and "300500" in html


def test_lista_completa_paginada(origen, historia_cloruro, estudio_en_origen, cliente_bioquimico):
    pendientes_en(origen, estudio_en_origen, 30)
    url = reverse("estudios:desvios")
    pagina1 = html_de(cliente_bioquimico.get(url))
    assert "30 pendientes" in pagina1
    assert pagina1.count("data-desvio-fila") == 25
    pagina2 = html_de(cliente_bioquimico.get(url, {"page": 2}))
    assert pagina2.count("data-desvio-fila") == 5


def test_lista_vacia(cliente_bioquimico):
    html = html_de(cliente_bioquimico.get(reverse("estudios:desvios")))
    assert "No hay desvíos sin revisar" in html and "0 pendientes" in html


def test_enlaces(con_desvio, cliente_bioquimico, django_user_model):
    html = html_de(cliente_bioquimico.get(reverse("estudios:desvios")))
    inicio = html.index("data-desvio-fila")
    fila_html = html[inicio : html.index("</tr>", inicio)]
    muestra = con_desvio.muestra
    assert reverse("muestras:detalle", args=[muestra.pk]) in fila_html
    assert str(muestra.numero_pi) in fila_html
    assert muestra.cliente.nombre_completo in fila_html and muestra.origen.nombre in fila_html
    assert "Cloruro" in fila_html and "CL-" in fila_html
    assert "160 mg/l" in fila_html and "110 mg/l" in fila_html and "+45,5 %" in fila_html
    calculado = desvios.pendientes()[0].fecha_calculo
    assert timezone.localtime(calculado).strftime("%d/%m/%Y") in fila_html
    assert reverse("estudios:detalle", args=[con_desvio.pk]) in fila_html
    assert desvios.enlace_comparacion(con_desvio, "CL-") in fila_html
    validar_url = reverse("estudios:validar_resultados", args=[con_desvio.pk])
    assert validar_url in fila_html and "Validar" in fila_html

    administrador = usuario(django_user_model, "admin-desvios@ejemplo.com", "Administradores")
    html_admin = html_de(administrador.get(reverse("estudios:desvios")))
    assert "data-desvio-fila" in html_admin
    assert validar_url not in html_admin


def test_permisos_lista(cliente_bioquimico, django_user_model):
    url = reverse("estudios:desvios")
    anonimo = Client().get(url)
    assert anonimo.status_code == 302 and reverse("usuarios:login") in anonimo.url
    tecnico = usuario(django_user_model, "tecnico-lista@ejemplo.com")
    assert tecnico.get(url).status_code == 403
    assert cliente_bioquimico.post(url).status_code == 405


def test_consultas_dashboard_y_lista(
    origen, historia_cloruro, estudio_en_origen, cliente_bioquimico, django_assert_max_num_queries
):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    def contar():
        with CaptureQueriesContext(connection) as consultas:
            cliente_bioquimico.get(reverse("estudios:desvios"))
        return len(consultas.captured_queries)

    estudio_en_origen(origen, dia(10), 300500, {"CL-": "16", "PH": "7.0"}, validar_todo=False)
    uno = contar()
    estudio_en_origen(origen, dia(11), 300501, {"CL-": "16", "PH": "7.0"}, validar_todo=False)
    dos = contar()
    estudio_en_origen(origen, dia(12), 300502, {"CL-": "16", "PH": "7.0"}, validar_todo=False)
    tres = contar()
    # Crece por estudio (una evaluación cada uno), no por prueba.
    assert dos - uno == tres - dos
