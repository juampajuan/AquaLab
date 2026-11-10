"""Inicio personalizado: rol profesional independiente de permisos y Administración."""

import re

import pytest
from django.contrib.auth.models import Group, Permission
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from estudios.models import Estudio
from estudios.tests.conftest import (
    cliente_a as cliente_a,
)
from estudios.tests.conftest import (
    crear_pendiente as crear_pendiente,
)
from estudios.tests.conftest import (
    empleado as empleado,
)
from estudios.tests.conftest import (
    firma_de as firma_de,
)
from estudios.tests.conftest import (
    muestra as muestra,
)
from informes.servicios import EmitirInformeError, emitir_informe

pytestmark = pytest.mark.django_db


def inicio(client, usuario):
    client.force_login(usuario)
    return client.get(reverse("inicio"))


def indicadores(response):
    return {
        n: int(v)
        for n, v in re.findall(
            r'data-indicador="([^"]+)".*?data-valor>(\d+)<', response.content.decode(), re.S
        )
    }


def grupo(usuario, nombre):
    usuario.groups.add(Group.objects.get_or_create(name=nombre)[0])


def permiso(usuario, nombre):
    app, codename = nombre.split(".")
    usuario.user_permissions.add(
        Permission.objects.get(content_type__app_label=app, codename=codename)
    )


def test_carga_sin_iniciar_y_parcial(client, empleado, crear_pendiente):
    crear_pendiente()
    crear_pendiente(cargadas=1)
    assert indicadores(inicio(client, empleado)) == {"mediciones-pendientes": 2}


def test_tecnico_solo_mediciones(client, empleado, crear_pendiente):
    crear_pendiente(cargadas=1)
    r = inicio(client, empleado)
    assert indicadores(r) == {"mediciones-pendientes": 1}
    assert "Validar resultados" not in r.content.decode()


def test_bioquimico_tres_unidades(client, crear_pendiente):
    crear_pendiente(cargadas=1)
    crear_pendiente(cantidad=1, cargadas=1, completado=True)
    assert indicadores(inicio(client, crear_pendiente.profesional)) == {
        "mediciones-pendientes": 1,
        "resultados-por-validar": 1,
        "estudios-listos": 1,
    }


def test_ceros_con_enlaces(client, crear_pendiente):
    r = inicio(client, crear_pendiente.profesional)
    assert indicadores(r) == {
        "mediciones-pendientes": 0,
        "resultados-por-validar": 0,
        "estudios-listos": 0,
    }
    for url in (
        "/estudios/buscar/?pendiente=mediciones",
        "/estudios/buscar/?pendiente=validaciones",
        "/informes/?listos=1",
    ):
        assert f'href="{url}"' in r.content.decode()
        assert client.get(url).context["page_obj"].paginator.count == 0


def test_validacion_cinco_mas_uno(client, crear_pendiente):
    crear_pendiente(cantidad=5, cargadas=5)
    crear_pendiente(cantidad=1, cargadas=1)
    crear_pendiente()
    assert indicadores(inicio(client, crear_pendiente.profesional))["resultados-por-validar"] == 6


def test_administrador_comun(client, empleado):
    grupo(empleado, "Administradores")
    assert indicadores(inicio(client, empleado)) == {"mediciones-pendientes": 0}


def test_administrador_bioquimico(client, crear_pendiente):
    profesional = crear_pendiente.profesional
    grupo(profesional, "Administradores")
    assert len(indicadores(inicio(client, profesional))) == 3


@pytest.mark.parametrize("via", ["individual", "grupo", "superusuario"])
def test_permisos_no_sustituyen_grupo(client, empleado, crear_pendiente, via):
    if via == "superusuario":
        empleado.is_superuser = True
        empleado.save()
    elif via == "individual":
        permiso(empleado, "estudios.validar_resultados")
    else:
        otro = Group.objects.create(name="Validadores alternativos")
        otro.permissions.add(Permission.objects.get(codename="validar_resultados"))
        empleado.groups.add(otro)
    estudio = crear_pendiente(cargadas=1)
    assert indicadores(inicio(client, empleado)) == {"mediciones-pendientes": 1}
    assert client.get(reverse("estudios:validar_resultados", args=[estudio.pk])).status_code == 200


def test_bioquimico_sin_permiso_operativo(client, empleado, crear_pendiente):
    grupo(empleado, "Bioquímicos")
    Group.objects.get(name="Bioquímicos").permissions.clear()
    estudio = crear_pendiente(cargadas=1)
    assert len(indicadores(inicio(client, empleado))) == 3
    assert client.get(reverse("estudios:buscar")).status_code == 200
    assert client.get(reverse("estudios:validar_resultados", args=[estudio.pk])).status_code == 403
    assert client.post(reverse("informes:generar", args=[estudio.pk])).status_code == 403


def test_firma_no_cambia_listos(client, empleado, crear_pendiente):
    estudio = crear_pendiente(cantidad=1, cargadas=1, completado=True)
    grupo(empleado, "Bioquímicos")
    r = inicio(client, empleado)
    assert indicadores(r)["estudios-listos"] == 1
    with pytest.raises(EmitirInformeError, match="firma"):
        emitir_informe(estudio.pk, empleado)


def test_cuenta_inactiva_y_sesion_revocada(client, empleado):
    assert inicio(client, empleado).status_code == 200
    empleado.is_active = False
    empleado.save()
    for url in (
        "/",
        "/estudios/buscar/?pendiente=validaciones",
        "/informes/",
        "/informes/dashboard/",
    ):
        assert client.get(url).status_code == 302
    assert not client.login(email=empleado.email, password="Clave-Valida-123")


def test_cambio_grupo_siguiente_request(client, empleado):
    r = inicio(client, empleado)
    assert r.context["huella_sesion"]
    assert "no-store" in r["Cache-Control"]
    assert len(indicadores(r)) == 1
    grupo(empleado, "Bioquímicos")
    assert len(indicadores(client.get("/"))) == 3
    empleado.groups.clear()
    assert len(indicadores(client.get("/"))) == 1


def test_consultas_inicio_no_crecen(client, empleado, crear_pendiente):
    crear_pendiente(cargadas=1)
    inicio(client, empleado)
    with CaptureQueriesContext(connection) as pocas:
        client.get("/")
    for _ in range(5):
        crear_pendiente(cargadas=1)
    with CaptureQueriesContext(connection) as muchas:
        client.get("/")
    assert len(pocas) == len(muchas)
    inicio(client, crear_pendiente.profesional)
    with CaptureQueriesContext(connection) as pocas_bio:
        client.get("/")
    crear_pendiente(cargadas=1)
    with CaptureQueriesContext(connection) as muchas_bio:
        client.get("/")
    assert len(pocas_bio) == len(muchas_bio)


def test_tecnico_no_consulta_contadores_profesionales(client, empleado, monkeypatch):
    def prohibido(*args, **kwargs):
        pytest.fail("El técnico no necesita consultar contadores profesionales")

    monkeypatch.setattr("config.views.resultados_por_validar", prohibido)
    monkeypatch.setattr("config.views.estudios_para_informar", prohibido)
    assert inicio(client, empleado).status_code == 200


def test_enlace_listos_reusa_filtro(client, crear_pendiente):
    esperado = {crear_pendiente(cantidad=1, cargadas=1, completado=True).pk for _ in range(22)}
    crear_pendiente(cantidad=1, cargadas=1, informado=True)
    r = inicio(client, crear_pendiente.profesional)
    i = next(i for i in r.context["indicadores"] if i["nombre"] == "estudios-listos")
    assert i["url"] == "/informes/?listos=1"
    assert i["valor"] == 22
    primera = client.get(i["url"])
    segunda = client.get(i["url"] + "&page=2")
    assert {e.pk for e in primera.context["page_obj"]} | {
        e.pk for e in segunda.context["page_obj"]
    } == esperado


def accesos(response):
    return re.search(
        r'data-componente="accesos"(.*?)</section>', response.content.decode(), re.S
    ).group(1)


def test_orden_grupos(client, empleado):
    assert re.findall(r'data-modulo="([^"]+)"', accesos(inicio(client, empleado))) == [
        "Clientes",
        "Muestras",
        "Estudios",
        "Informes",
    ]


def test_accesos_por_modulo(client, empleado):
    html = accesos(inicio(client, empleado))
    esperados = {
        "Clientes": ["clientes:buscar", "clientes:registrar"],
        "Muestras": ["muestras:registrar"],
        "Estudios": ["estudios:crear", "estudios:buscar"],
        "Informes": ["informes:listar"],
    }
    for modulo, rutas in esperados.items():
        bloque = re.search(r'data-modulo="' + modulo + r'"(.*?)(?=data-modulo=|$)', html, re.S)
        assert bloque
        for ruta in rutas:
            assert f'href="{reverse(ruta)}"' in bloque.group(1)
            assert html.count(f'href="{reverse(ruta)}"') == 1


@pytest.mark.parametrize("autorizado", [False, True])
def test_gestion_tipos_permiso(client, empleado, autorizado):
    if autorizado:
        permiso(empleado, "estudios.gestionar_catalogo")
    html = accesos(inicio(client, empleado))
    assert (reverse("estudios:tipos_listar") in html) == autorizado
    if autorizado:
        assert html.index('data-modulo="Estudios"') < html.index(reverse("estudios:tipos_listar"))
        assert html.index(reverse("estudios:tipos_listar")) < html.index('data-modulo="Informes"')
    assert client.get(reverse("estudios:tipos_listar")).status_code == (200 if autorizado else 403)


def test_navegacion_no_muta(client, empleado, crear_pendiente):
    from estudios.models import Medicion, Resultado, Validacion
    from informes.models import Informe

    crear_pendiente(cargadas=1)
    modelos = [Estudio, Medicion, Resultado, Validacion, Informe]
    antes = [m.objects.count() for m in modelos]
    inicio(client, empleado)
    for ruta in (
        "clientes:buscar",
        "clientes:registrar",
        "muestras:registrar",
        "estudios:crear",
        "estudios:buscar",
        "informes:listar",
    ):
        assert client.get(reverse(ruta)).status_code == 200
    assert [m.objects.count() for m in modelos] == antes


def test_tarjeta_dashboard_autorizado(client, crear_pendiente):
    r = inicio(client, crear_pendiente.profesional)
    assert "Ver dashboard" in r.content.decode()
    assert client.get(reverse("informes:dashboard")).status_code == 200


def test_sin_dashboard(client, empleado):
    r = inicio(client, empleado)
    assert "Ver dashboard" not in r.content.decode()
    assert client.get(reverse("informes:dashboard")).status_code == 403


@pytest.mark.parametrize(
    "via", ["individual", "administrador", "otro_grupo", "superusuario", "bio_sin_permiso"]
)
def test_dashboard_independiente_rol(client, empleado, via):
    if via == "superusuario":
        empleado.is_superuser = True
        empleado.save()
    elif via == "individual":
        permiso(empleado, "informes.ver_dashboard")
    elif via == "otro_grupo":
        g = Group.objects.create(name="Supervisión alternativa")
        g.permissions.add(Permission.objects.get(codename="ver_dashboard"))
        empleado.groups.add(g)
    elif via == "administrador":
        grupo(empleado, "Administradores")
    else:
        grupo(empleado, "Bioquímicos")
        Group.objects.get(name="Bioquímicos").permissions.clear()
    r = inicio(client, empleado)
    permitido = via != "bio_sin_permiso"
    assert ("Ver dashboard" in r.content.decode()) == permitido
    assert client.get(reverse("informes:dashboard")).status_code == (200 if permitido else 403)
    assert len(indicadores(r)) == (3 if via == "bio_sin_permiso" else 1)


def test_revocacion_dashboard_siguiente_request(client, empleado):
    permiso(empleado, "informes.ver_dashboard")
    assert "Ver dashboard" in inicio(client, empleado).content.decode()
    empleado.user_permissions.clear()
    assert "Ver dashboard" not in client.get("/").content.decode()
    assert client.get(reverse("informes:dashboard")).status_code == 403
