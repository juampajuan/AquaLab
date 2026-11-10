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
    return Origen.objects.create(cliente=cliente_a, nombre="Pozo de control")


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
    assert fecha in cloruro and ">Repetida</span>" in cloruro
    assert "Mediana 110 mg/l, umbral 30 %" in cloruro
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


# --- Validación con desvíos (US 3, FR-007 y FR-008) ------------------------------------------


def url_validar(estudio):
    return reverse("estudios:validar_resultados", args=[estudio.pk])


@pytest.fixture
def tres_pruebas(origen, estudio_en_origen):
    """Sin validar: Cloruro 160 y pH 9,5 con desvío; Conductividad 500 sin desvío."""
    for n in range(3):
        estudio_en_origen(origen, dia(n), 300801 + n, {"CL-": "10", "PH": "7.0", "COND": "500"})
    return estudio_en_origen(
        origen, dia(3), 300810, {"CL-": "16", "PH": "9.5", "COND": "500"}, validar_todo=False
    )


def envio(estudio, accion, codigos, observaciones=None):
    datos = {"accion": accion}
    for codigo in codigos:
        asignacion = asignacion_de(estudio, codigo)
        datos[f"validar_{asignacion.pk}"] = "on"
        datos[f"resultado_{asignacion.pk}"] = str(asignacion.resultado.valor)
    for codigo, texto in (observaciones or {}).items():
        datos[f"observacion_{asignacion_de(estudio, codigo).pk}"] = texto
    return datos


def test_validacion_destaca_desvios(con_desvio, cliente_bioquimico):
    html = html_de(cliente_bioquimico.get(url_validar(con_desvio)))
    assert "1 prueba con desvío" in html
    cl = asignacion_de(con_desvio, "CL-")
    cloruro = fila(html, "CL-")
    assert 'data-desvio="pendiente"' in cloruro and "Observado 160 mg/l" in cloruro
    assert "Mediana de los últimos 3: 110 mg/l" in cloruro
    assert desvios.enlace_comparacion(con_desvio, "CL-") in cloruro
    assert f'name="observacion_{cl.pk}"' in cloruro
    assert "Queda guardada en la validación de esta prueba" in cloruro
    ph = fila(html, "PH")
    assert "observacion_" not in ph and "data-desvio" not in ph


def test_historial_insuficiente_en_validacion(origen, estudio_en_origen, cliente_bioquimico):
    estudio_en_origen(origen, dia(0), 300801, {"CL-": "10"})
    estudio_en_origen(origen, dia(1), 300802, {"CL-": "11"})
    actual = estudio_en_origen(origen, dia(2), 300803, {"CL-": "40"}, validar_todo=False)
    html = html_de(cliente_bioquimico.get(url_validar(actual)))
    assert "Historial insuficiente para detectar desvíos" in fila(html, "CL-")
    assert "prueba con desvío" not in html


def test_confirmacion_cuenta_desvios_elegidos(tres_pruebas, cliente_bioquimico):
    datos = envio(tres_pruebas, "revisar", ["CL-", "PH", "COND"], {"CL-": "Repetida"})
    html = html_de(cliente_bioquimico.post(url_validar(tres_pruebas), datos))
    assert "2 de los 3 resultados elegidos tienen desvío: quedarán revisados al validar." in html
    assert "Repetida" in html and "Sin observación" in html
    cl = asignacion_de(tres_pruebas, "CL-")
    assert f'name="observacion_{cl.pk}" value="Repetida"' in html

    una = envio(tres_pruebas, "revisar", ["CL-", "COND"])
    html = html_de(cliente_bioquimico.post(url_validar(tres_pruebas), una))
    assert "1 de los 2 resultados elegidos tiene desvío: quedará revisado al validar." in html


def test_observacion_larga_no_avanza(con_desvio, cliente_bioquimico):
    datos = envio(con_desvio, "revisar", ["CL-"], {"CL-": "x" * 501})
    respuesta = cliente_bioquimico.post(url_validar(con_desvio), datos)
    assert "estudios/validar_resultados.html" in [t.name for t in respuesta.templates]
    cl = asignacion_de(con_desvio, "CL-")
    assert f'id="id_observacion_{cl.pk}_error"' in html_de(respuesta)


def test_editar_conserva_observacion(con_desvio, cliente_bioquimico):
    datos = envio(con_desvio, "editar", ["CL-"], {"CL-": "Repetida"})
    html = html_de(cliente_bioquimico.post(url_validar(con_desvio), datos))
    inicio = html.index(f'name="observacion_{asignacion_de(con_desvio, "CL-").pk}"')
    assert "Repetida" in html[inicio : html.index("</textarea>", inicio)]


def test_confirmar_avisa_revisados(con_desvio, cliente_bioquimico):
    datos = envio(con_desvio, "confirmar", ["CL-", "PH"], {"CL-": "Repetida"})
    respuesta = cliente_bioquimico.post(url_validar(con_desvio), datos, follow=True)
    html = html_de(respuesta)
    assert "Se revisó 1 desvío: CL-." in html
    validacion = Validacion.objects.get(asignacion=asignacion_de(con_desvio, "CL-"), anulada=False)
    assert validacion.observacion == "Repetida" and validacion.con_desvio
    assert 'data-desvio="revisado"' in fila(html, "CL-")


def test_permisos(con_desvio, django_user_model):
    from django.urls import NoReverseMatch

    with pytest.raises(NoReverseMatch):
        reverse("estudios:revisar_desvio", args=[con_desvio.pk, 1])
    tecnico = usuario(django_user_model, "tecnico-validar@ejemplo.com")
    assert tecnico.get(url_validar(con_desvio)).status_code == 403


# --- No bloquea ni sale al cliente (US 4, FR-012) --------------------------------------------


def test_no_aparece_en_informe_pdf_ni_correo(con_desvio, bioquimico, cliente_bioquimico):
    from informes.contenido import armar_contenido
    from informes.envios import mensaje_de_correo
    from informes.servicios import emitir_informe

    validar_url = url_validar(con_desvio)
    datos = envio(con_desvio, "confirmar", ["CL-", "PH"], {"CL-": "Observación interna"})
    # follow=True consume el mensaje «Se revisó 1 desvío» en el detalle del estudio.
    cliente_bioquimico.post(validar_url, datos, follow=True)
    con_desvio.refresh_from_db()

    textos = [
        html_de(cliente_bioquimico.get(reverse("informes:vista_previa", args=[con_desvio.pk]))),
        html_de(cliente_bioquimico.get(reverse("informes:control", args=[con_desvio.pk]))),
        str(armar_contenido(con_desvio)),
    ]
    informe = emitir_informe(con_desvio.pk, bioquimico)
    textos += [
        html_de(cliente_bioquimico.get(reverse("informes:ver", args=[con_desvio.pk]))),
        html_de(cliente_bioquimico.get(reverse("informes:imprimir", args=[con_desvio.pk]))),
        mensaje_de_correo(informe, "cliente@ejemplo.com", b"%PDF").body,
    ]
    for texto in textos:
        assert "esvío" not in texto
        assert "Observación interna" not in texto


# --- Regla configurable (US 5) ---------------------------------------------------------------


def test_cambio_de_regla_conserva_constancia(con_desvio, cliente_bioquimico, settings):
    datos = envio(con_desvio, "confirmar", ["CL-"])
    cliente_bioquimico.post(url_validar(con_desvio), datos)
    settings.AQUALAB_DESVIOS = {"umbral": "50", "cantidad": 3}
    html = html_de(cliente_bioquimico.get(reverse("estudios:detalle", args=[con_desvio.pk])))
    assert "umbral 30 %" in fila(html, "CL-")


def test_texto_regla_vigente(con_desvio, cliente_bioquimico, settings):
    settings.AQUALAB_DESVIOS = {"umbral": "40", "cantidad": 3}
    regla = "más de un 40 % respecto de la mediana de los últimos 3 resultados validados del origen"
    for url in (reverse("estudios:desvios"), url_validar(con_desvio)):
        assert regla in html_de(cliente_bioquimico.get(url))
