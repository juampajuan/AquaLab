import re

import pytest
from django.urls import reverse

from informes.models import Informe

pytestmark = pytest.mark.django_db

URL = reverse("informes:emitidos")


def filas(respuesta):
    """Números de informe que aparecen en la tabla, en orden."""
    return re.findall(r"(INF-\d{6})</a>", respuesta.content.decode())


def test_menu_informes_emitidos(cliente_http, tres_informes):
    html = cliente_http.get(reverse("inicio")).content.decode()
    assert f'href="{URL}"' in html
    assert "Informes emitidos" in html
    for url in (URL, reverse("informes:ver", args=[tres_informes[0].estudio_id])):
        html = cliente_http.get(url).content.decode()
        enlace = re.search(rf'<a href="{URL}"[^>]*>', html).group(0)
        assert 'aria-current="page"' in enlace


def test_listado_columnas_y_orden(cliente_http, tres_informes, con_fecha):
    uno, dos, tres = tres_informes
    con_fecha(dos, 2026, 10, 5, hora=9, minuto=15)
    respuesta = cliente_http.get(URL)
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert filas(respuesta) == ["INF-000003", "INF-000002", "INF-000001"]
    assert "05/10/2026 09:15" in html
    assert "José Núñez" in html and "DNI 28444555" in html
    assert "Aguas del Sur SA" in html
    assert "200102" in html
    assert f"#{dos.estudio_id}" in html
    assert dos.contenido["estudio"]["tipo"] in html
    assert dos.contenido["firma"]["nombre"] in html
    assert f'href="{reverse("informes:ver", args=[dos.estudio_id])}"' in html


def test_emitido_por_sin_firma_usa_el_usuario(cliente_http, tres_informes):
    uno = tres_informes[0]
    contenido = {k: v for k, v in uno.contenido.items() if k != "firma"}
    Informe.objects.filter(pk=uno.pk).update(contenido=contenido)
    uno.emitido_por.first_name = "Nombre"
    uno.emitido_por.last_name = "Guardado"
    uno.emitido_por.save()
    html = cliente_http.get(URL, {"q": "1"}).content.decode()
    assert "Nombre Guardado" in html


def test_paginacion_conserva_filtros(cliente_http, otra_muestra, emitir_de):
    muestra = otra_muestra(200201, "Cliente Paginado", "27111222")
    for _ in range(21):
        emitir_de(muestra)
    parametros = {"q": "paginado", "desde": "2020-01-01", "hasta": "2099-12-31"}
    respuesta = cliente_http.get(URL, parametros)
    assert len(filas(respuesta)) == 20
    html = respuesta.content.decode()
    assert "q=paginado&amp;desde=2020-01-01&amp;hasta=2099-12-31&page=2" in html
    segunda = cliente_http.get(URL, parametros | {"page": 2})
    assert filas(segunda) == ["INF-000001"]


@pytest.mark.parametrize(
    ("parametros", "mensaje"),
    [
        ({}, "Todavía no hay informes emitidos."),
        ({"q": "nadie"}, "No hay informes que coincidan con la búsqueda."),
    ],
)
def test_listado_vacio(cliente_http, parametros, mensaje):
    html = cliente_http.get(URL, parametros).content.decode()
    assert mensaje in html


def test_listado_vacio_con_filtros_y_sin_coincidencias(cliente_http, tres_informes):
    html = cliente_http.get(URL, {"q": "nadie"}).content.decode()
    assert "No hay informes que coincidan con la búsqueda." in html


@pytest.mark.parametrize(
    ("parametros", "mensaje"),
    [
        ({"desde": "31/02/2026"}, "Introduzca una fecha válida."),
        (
            {"desde": "2026-10-09", "hasta": "2026-10-01"},
            "La fecha desde no puede ser posterior a la fecha hasta.",
        ),
    ],
)
def test_fechas_invalidas(cliente_http, tres_informes, parametros, mensaje):
    respuesta = cliente_http.get(URL, parametros)
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert mensaje in html
    assert filas(respuesta) == []


def test_fechas_en_formato_argentino(cliente_http, tres_informes, con_fecha):
    con_fecha(tres_informes[0], 2026, 10, 1)
    respuesta = cliente_http.get(URL, {"desde": "01/10/2026", "hasta": "01/10/2026"})
    assert filas(respuesta) == ["INF-000001"]


def test_cualquier_empleado_ve_el_listado(cliente_http, tres_informes):
    assert cliente_http.get(URL).status_code == 200
