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
from informes import tablero
from informes.models import Informe
from muestras.models import Muestra, Origen

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
    assert ("data-calidad" in html_de(respuesta)) == (estado == 200)  # US 8.4
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


def test_rango_del_periodo_legible(cliente_bioquimico):
    """Observación del sprint 4: arriba se lee el período y contra cuál se compara."""
    periodo = tablero.periodo("este_mes", timezone.localdate())
    html = html_de(cliente_bioquimico.get(URL))
    assert f'Período:</dt> <dd class="inline" data-rango-actual>{periodo.rango_texto}' in html
    assert (
        f'Comparado con:</dt> <dd class="inline" data-rango-anterior>'
        f"{periodo.rango_anterior_texto}" in html
    )


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
    assert "antes 0" in html  # la demo no tiene datos 6 meses antes
    assert "sin datos previos" not in html
    assert "Estudios por estado" in html
    for estado in ("Sin iniciar", "En proceso", "Finalizado", "Informe generado"):
        assert estado in html


def test_cada_indicador_muestra_el_valor_anterior(cliente_bioquimico, con_demo):
    """Observación del sprint 4: una sola línea corta, «antes 7 · ▲ +1»; el período de
    comparación se lee una vez, arriba."""
    html = html_de(cliente_bioquimico.get(URL + "?periodo=ultimos_3"))
    for nombre in ("muestras", "estudios", "informes", "respuesta"):
        tarjeta = bloque(html, f'data-indicador="{nombre}"')
        assert f'id="ayuda-indicador-{nombre}"' in tarjeta
        assert "vs." not in tarjeta
    for nombre in ("muestras", "estudios", "informes"):
        tarjeta = bloque(html, f'data-indicador="{nombre}"')
        assert re.search(r"data-antes>antes \d+</span> ·", tarjeta)
        assert re.search(r'data-tono="(exito|peligro|neutro)">[▲▼=] [+−]?\d+<', tarjeta)


def test_sin_datos_para_comparar(cliente_bioquimico):
    tarjeta = bloque(html_de(cliente_bioquimico.get(URL)), 'data-indicador="respuesta"')
    assert "Sin datos para comparar" in tarjeta
    assert "data-antes" not in tarjeta


def test_graficos_y_secciones_con_ayuda(cliente_bioquimico):
    html = html_de(cliente_bioquimico.get(URL))
    for ayuda in (
        "ayuda-estados",
        "ayuda-grafico-respuesta",
        "ayuda-grafico-actividad",
        "ayuda-calidad",
        "ayuda-desvios-dashboard",
    ):
        assert f'id="{ayuda}"' in html
    assert "por fecha de emisión" in html and "por fecha de ingreso" in html


def test_secciones_agrupadas_por_periodo(cliente_bioquimico):
    """Lo que usa el período va junto, arriba; lo demás, en un bloque aparte con una sola
    aclaración (en vez de repetir «no depende del período» en cada sección)."""
    html = html_de(cliente_bioquimico.get(URL))
    periodo, general = html.index("data-bloque-periodo"), html.index("data-bloque-general")
    for marca in ('name="periodo"', 'data-indicador="muestras"', "data-calidad"):
        assert periodo < html.index(marca) < general
    for marca in (
        'aria-labelledby="titulo-estados"',
        'aria-labelledby="titulo-respuesta"',
        'aria-labelledby="titulo-actividad"',
        "data-comparacion-historica",
        "data-desvios",
    ):
        assert general < html.index(marca)
    assert "no cambian con el período elegido" in html
    assert "no depende del período" not in html


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
    vigentes = Validacion.objects.filter(anulada=False).count()
    respuesta = cliente_bioquimico.get(URL + "?periodo=ultimos_3")
    assert "data-calidad" in html_de(respuesta)  # la sección «Calidad» (US 8.4) tampoco escribe
    assert [m.objects.count() for m in modelos] == antes
    assert Validacion.objects.filter(anulada=False).count() == vigentes


def test_cantidad_de_consultas(cliente_bioquimico, con_demo, django_assert_max_num_queries):
    from estudios.models import EstadoPruebaEstudio, PruebaEstudio

    # «Desvíos sin revisar» (US 8.2) suma una consulta y una evaluación de cantidad fija (6
    # consultas de la comparación histórica) por estudio con resultados sin validar; «Calidad»
    # (US 8.4), 7 consultas fijas.
    con_pendientes = (
        PruebaEstudio.objects.filter(estado=EstadoPruebaEstudio.CARGADA, resultado__isnull=False)
        .values("estudio")
        .distinct()
        .count()
    )
    with django_assert_max_num_queries(25 + 1 + 7 + 6 * con_pendientes):
        assert cliente_bioquimico.get(URL).status_code == 200


def test_tarjeta_comparacion_historica(cliente_bioquimico, cliente_a):
    """US 8.1: el dashboard elige cliente y origen para la comparación histórica."""
    import json

    from clientes.models import Cliente

    pozo = Origen.objects.create(cliente=cliente_a, nombre="Pozo del dashboard")
    inactivo = Cliente.objects.create(
        nombre="Cliente inactivo",
        tipo_documento="DNI",
        numero_documento="30111222",
        email="inactivo@ejemplo.com",
        activo=False,
    )
    Origen.objects.create(cliente=inactivo, nombre="Origen inactivo")

    html = html_de(cliente_bioquimico.get(URL))

    tarjeta = re.search(r"<section[^>]*data-comparacion-historica.*?</section>", html, re.S)
    assert tarjeta
    tarjeta = tarjeta.group(0)
    assert "Comparación histórica" in tarjeta
    assert re.search(
        rf'<form method="get" action="{reverse("estudios:comparacion")}"[^>]*data-elegir-origen',
        tarjeta,
    )
    assert 'name="cliente"' in tarjeta and 'name="origen"' in tarjeta
    assert f'<optgroup label="{cliente_a.nombre_completo}">' in tarjeta
    assert "Ver evolución" in tarjeta
    assert "Origen inactivo" not in tarjeta
    datos = re.search(
        r'<script id="origenes-por-cliente" type="application/json">(.*?)</script>', html, re.S
    )
    assert json.loads(datos.group(1)) == {str(cliente_a.pk): [[pozo.pk, "Pozo del dashboard"]]}


# --- Desvíos sin revisar (US 8.2) ------------------------------------------------------------


def test_seccion_desvios_sin_revisar(cliente_bioquimico, estudio_en_origen, cliente_a):
    from estudios import desvios

    origen = Origen.objects.create(cliente=cliente_a, nombre="Pozo del dashboard")
    for n, valor in enumerate(["10", "11", "12"]):
        estudio_en_origen(origen, dt.date(2026, 3, 1 + n), 300601 + n, {"CL-": valor})
    estudio_en_origen(origen, dt.date(2026, 3, 5), 300610, {"CL-": "16"}, validar_todo=False)

    html = html_de(cliente_bioquimico.get(URL))
    assert 'aria-labelledby="titulo-desvios"' in html
    cantidad = len(desvios.pendientes())
    assert cantidad == 1
    assert f"{cantidad} pendiente<" in html


# --- Calidad (US 8.4) --------------------------------------------------------------------------


def seccion_calidad(html):
    seccion = re.search(r"<section[^>]*data-calidad.*?</section>", html, re.S)
    assert seccion, "falta la sección «Calidad»"
    return seccion.group(0)


def bloque(html, atributo):
    """El elemento que lleva `atributo` y lo que contiene hasta su cierre (div)."""
    inicio = html.index(atributo)
    resto = html[inicio:]
    profundidad, posicion = 0, 0
    for marca in re.finditer(r"<div\b|</div>", resto):
        profundidad += 1 if marca.group(0) == "<div" else -1
        if profundidad < 0:
            posicion = marca.end()
            break
    return resto[:posicion] if posicion else resto


def test_indicador_calidad_en_pantalla(cliente_bioquimico, evaluadas):
    evaluadas({"PH": (0, 10), "TURBIDEZ": (0, 10), "COLOR": (0, 10), "CL-": (4, 10)})
    evaluadas({}, sin_limite={"COND": 3})
    evaluadas({"CL-": (1, 1)}, momento=timezone.now() - dt.timedelta(days=75))

    seccion = seccion_calidad(html_de(cliente_bioquimico.get(URL)))

    assert seccion.index('aria-labelledby="titulo-calidad"') < seccion.index("Calidad")
    assert 'id="ayuda-calidad"' in seccion
    indicador = bloque(seccion, 'data-indicador="calidad"')
    assert "data-valor>10,0 %</span>" in indicador
    assert "4 de 40 resultados" in indicador
    assert "% de resultados fuera de norma" in indicador
    assert "Nivel de cumplimiento" not in indicador
    assert 'id="ayuda-indicador-calidad"' in indicador
    assert re.search(r'data-tono="(exito|peligro|neutro)"', indicador)
    assert "Sin datos para comparar" in indicador
    assert "ayuda-puntos-porcentuales" not in indicador  # sin variación no hace falta
    assert "3 sin límite para comparar (no se cuentan)" in bloque(seccion, "data-sin-limite")

    seccion = seccion_calidad(html_de(cliente_bioquimico.get(URL + "?periodo=ultimos_6")))
    indicador = bloque(seccion, 'data-indicador="calidad"')
    assert "data-valor>12,2 %</span>" in indicador
    assert "5 de 41 resultados" in indicador


def test_variacion_de_calidad_explicada(cliente_bioquimico, evaluadas):
    """Observación del sprint 4: «▲ +4,9 p. p.» con el valor anterior y qué es «p. p.»."""
    ahora = timezone.localtime().replace(hour=12, minute=0, second=0, microsecond=0)
    evaluadas({"CL-": (7, 47)}, momento=ahora)  # 14,9 %
    mes_pasado = tablero.correr_meses(ahora.date(), -1)  # dentro de «los mismos días» del anterior
    evaluadas(
        {"PH": (1, 10)},
        momento=ahora.replace(year=mes_pasado.year, month=mes_pasado.month, day=mes_pasado.day),
    )
    seccion = seccion_calidad(html_de(cliente_bioquimico.get(URL)))
    indicador = bloque(seccion, 'data-indicador="calidad"')
    assert "▲ +4,9 p. p." in indicador
    assert "data-antes>antes 10,0 %</span> ·" in indicador
    assert 'id="ayuda-puntos-porcentuales"' in indicador
    assert "10 % → 14,9 % = +4,9 p. p." in indicador


def test_seccion_calidad_ubicacion(cliente_bioquimico):
    html = html_de(cliente_bioquimico.get(URL))
    assert (
        html.index('data-indicador="respuesta"')
        < html.index("data-calidad")
        < html.index('aria-labelledby="titulo-estados"')
    )


def test_seccion_sin_datos(cliente_bioquimico):
    respuesta = cliente_bioquimico.get(URL)
    assert respuesta.status_code == 200
    seccion = seccion_calidad(html_de(respuesta))
    assert "Sin resultados validados en el período" in seccion
    assert 'data-indicador="calidad"' in seccion
    assert "grafico-calidad-pruebas" not in seccion


def test_ranking_en_pantalla(cliente_bioquimico, evaluadas):
    import json

    evaluadas({"CL-": (2, 10), "ECOLI": (2, 8), "PH": (3, 4)})

    html = html_de(cliente_bioquimico.get(URL))
    seccion = seccion_calidad(html)
    ranking = bloque(seccion, 'data-ranking="pruebas"')
    assert "Solo pruebas con al menos 5 resultados evaluados" in ranking
    assert '<canvas id="grafico-calidad-pruebas"' in ranking
    assert re.search(r"<details[^>]*>\s*<summary[^>]*>Ver datos</summary>", ranking)
    assert "ECOLI · E. Coli" in ranking
    assert "25,0 % (2 de 8)" in ranking
    assert "20,0 % (2 de 10)" in ranking
    assert ranking.index("25,0 % (2 de 8)") < ranking.index("20,0 % (2 de 10)")
    assert "PH · pH" not in ranking
    assert "pruebas más" not in ranking
    datos = re.search(
        r'<script id="datos-dashboard" type="application/json">(.*?)</script>', html, re.S
    )
    graficos = json.loads(datos.group(1))
    assert graficos["calidad_pruebas"]["porcentajes"] == ["25.0", "20.0"]
    assert "respuesta" in graficos and "actividad" in graficos


def test_ranking_restantes_en_pantalla(cliente_bioquimico, evaluadas):
    codigos = (
        "AG",
        "AL",
        "BO",
        "CA",
        "CADMIO",
        "CL-",
        "COBRE",
        "COLOR",
        "COND",
        "IAC",
        "PH",
        "TURBIDEZ",
    )
    evaluadas(dict.fromkeys(codigos, (1, 5)))

    ranking = bloque(
        seccion_calidad(html_de(cliente_bioquimico.get(URL))), 'data-ranking="pruebas"'
    )

    assert "Y 2 pruebas más" in ranking


def test_ranking_vacio_en_pantalla(cliente_bioquimico, evaluadas):
    evaluadas({"CL-": (0, 10), "PH": (3, 4)})

    ranking = bloque(
        seccion_calidad(html_de(cliente_bioquimico.get(URL))), 'data-ranking="pruebas"'
    )

    assert (
        "Ninguna prueba con al menos 5 resultados evaluados tuvo incumplimientos en el período."
        in ranking
    )
    assert "grafico-calidad-pruebas" not in ranking


def test_vertidos_en_pantalla(cliente_bioquimico, evaluadas):
    import json

    from muestras.models import TipoVertido

    evaluadas({"CL-": (1, 10)}, tipo_vertido=TipoVertido.AGUA)
    evaluadas({"CL-": (1, 1)}, tipo_vertido=TipoVertido.CLOACAL)

    html = html_de(cliente_bioquimico.get(URL))
    vertidos = bloque(seccion_calidad(html), "data-vertidos")
    assert "Pruebas evaluadas por tipo de vertido" in vertidos
    assert (
        "Cada prueba evaluada en el período suma una: una muestra con 7 pruebas aporta 7."
        in vertidos
    )
    assert 'aria-label="Pruebas que cumplen y fuera de norma por tipo de vertido"' in vertidos
    assert '<canvas id="grafico-calidad-vertidos"' in vertidos
    for encabezado in (
        "Tipo",
        "Pruebas evaluadas",
        "Pruebas que cumplen",
        "Pruebas fuera de norma",
        "Cumplimiento",
    ):
        assert f"<th>{encabezado}</th>" in vertidos
    assert "<th>Pruebas validadas</th>" not in vertidos
    nota = vertidos.split("data-nota-vertidos")[1]
    assert "No se cuentan las pruebas sin límite para comparar." in nota
    assert vertidos.index("</table>") < vertidos.index("data-nota-vertidos")
    filas = re.findall(r"<tr data-vertido=\"(\w+)\">(.*?)</tr>", vertidos, re.S)
    assert [valor for valor, _ in filas] == ["agua", "cloacal", "canal"]
    assert "90,0 %" in filas[0][1]
    assert "0,0 %" in filas[1][1]
    assert "Sin resultados" in filas[2][1]
    datos = re.search(
        r'<script id="datos-dashboard" type="application/json">(.*?)</script>', html, re.S
    )
    assert json.loads(datos.group(1))["calidad_vertidos"] == {
        "etiquetas": ["Agua", "Cloacal", "Canal"],
        "cumple": [9, 0, 0],
        "fuera": [1, 1, 0],
    }


def test_clientes_y_origenes_en_pantalla(cliente_bioquimico, evaluadas, cliente_a):
    from clientes.models import Cliente

    pozo = Origen.objects.create(cliente=cliente_a, nombre="Pozo con desvíos")
    evaluadas({"CL-": (3, 12)}, origen=pozo)
    inactivo = Cliente.objects.create(
        nombre="Cliente dado de baja",
        tipo_documento="DNI",
        numero_documento="30999888",
        email="baja@ejemplo.com",
        activo=False,
    )
    evaluadas({"CL-": (1, 1)}, origen=Origen.objects.create(cliente=inactivo, nombre="Pozo viejo"))

    seccion = seccion_calidad(html_de(cliente_bioquimico.get(URL)))
    clientes = bloque(seccion, 'data-ranking="clientes"')
    origenes = bloque(seccion, 'data-ranking="origenes"')

    assert "Clientes con más incumplimientos" in clientes
    assert "Orígenes con más incumplimientos" in origenes
    assert "3 de 12 · 25,0 %" in clientes and "3 de 12 · 25,0 %" in origenes
    historial = reverse("clientes:historial", args=[cliente_a.pk])
    comparacion = reverse("estudios:comparacion") + f"?cliente={cliente_a.pk}&amp;origen={pozo.pk}"
    assert f'href="{historial}"' in clientes
    assert f'href="{comparacion}"' in origenes
    assert cliente_bioquimico.get(historial).status_code == 200
    assert cliente_bioquimico.get(comparacion.replace("&amp;", "&")).status_code == 200
    for lista in (clientes, origenes):
        fila = re.search(r"<tr[^>]*>(?:(?!</tr>).)*Cliente dado de baja.*?</tr>", lista, re.S)
        assert fila and "Inactivo" in fila.group(0) and "<a " not in fila.group(0)


def test_clientes_y_origenes_vacios(cliente_bioquimico, evaluadas):
    evaluadas({"CL-": (0, 3)})

    seccion = seccion_calidad(html_de(cliente_bioquimico.get(URL)))

    for nombre in ("clientes", "origenes"):
        lista = bloque(seccion, f'data-ranking="{nombre}"')
        assert "No hubo resultados fuera de norma en el período." in lista
