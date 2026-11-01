import re

import pytest
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db

URL = reverse("informes:listar")


def filas(respuesta):
    """Números de estudio («#N») que aparecen en la tabla del listado, en orden."""
    return [int(n) for n in re.findall(r"#(\d+)</td>", respuesta.content.decode())]


@pytest.fixture
def tres_estudios(muestra, otra_muestra, estudio_para, completar, emitir):
    """Uno listo (Agua, 200001), uno en curso (200002) y uno con informe emitido (200003)."""
    listo = estudio_para(muestra, "CL-", "PH", "CA")
    completar(listo)
    en_curso = estudio_para(
        otra_muestra(200002, "Ana Pérez", "40111222", nombre="Pozo norte"), "CL-", "PH", "CA", "MG"
    )
    completar(en_curso, "CL-")
    emitido = estudio_para(
        otra_muestra(200003, "", "30711222", razon_social="Aguas del Sur SA"), "CL-"
    )
    completar(emitido)
    emitir(emitido)
    return listo, en_curso, emitido


def test_listado_muestra_estado_y_avance(cliente_http, tres_estudios):
    listo, en_curso, emitido = tres_estudios
    respuesta = cliente_http.get(URL)
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "Seleccionar estudio a informar" in html
    for estudio in tres_estudios:
        assert f"N° PI {estudio.muestra.numero_pi}" in html
        assert estudio.tipo_nombre_snapshot in html
        assert reverse("informes:control", args=[estudio.pk]) in html
    assert "Cliente de test" in html
    assert "3 de 3 pruebas completadas" in html
    assert "1 de 4 pruebas completadas" in html
    assert "1 de 1 prueba completada" in html
    assert 'data-estado="success">Informe generado' in html
    assert "Seleccionar</a>" in html


def test_listado_ordenado_y_paginado(cliente_http, estudio_de):
    estudios = [estudio_de("CL-") for _ in range(21)]
    pks = sorted((e.pk for e in estudios), reverse=True)
    primera = cliente_http.get(URL)
    assert filas(primera) == pks[:20]
    segunda = cliente_http.get(URL, {"page": 2})
    assert filas(segunda) == pks[20:]


@pytest.mark.parametrize(
    "busqueda",
    [
        "200002",  # N° PI
        "estudio",  # número de estudio (se reemplaza por el pk)
        "Ana Pérez",  # nombre del cliente
        "Aguas del Sur",  # razón social
        "40111222",  # documento del cliente
        "Pozo norte",  # nombre de la muestra
        "tipo",  # nombre del tipo (se reemplaza por el snapshot)
    ],
)
def test_busqueda_por_numero_pi_cliente_y_tipo(cliente_http, tres_estudios, busqueda):
    listo, en_curso, emitido = tres_estudios
    esperado = emitido if busqueda == "Aguas del Sur" else en_curso
    if busqueda == "estudio":
        busqueda = str(en_curso.pk)
    elif busqueda == "tipo":
        busqueda = en_curso.tipo_nombre_snapshot
    respuesta = cliente_http.get(URL, {"q": busqueda})
    assert filas(respuesta) == [esperado.pk]


def test_busqueda_sin_resultados(cliente_http, tres_estudios):
    respuesta = cliente_http.get(URL, {"q": "zzz"})
    assert filas(respuesta) == []
    assert "No se encontraron estudios" in respuesta.content.decode()


def test_busqueda_demasiado_larga(cliente_http, tres_estudios):
    respuesta = cliente_http.get(URL, {"q": "a" * 101})
    assert "Ingresá como máximo 100 caracteres para buscar." in respuesta.content.decode()


def test_filtro_solo_listos(cliente_http, tres_estudios):
    listo, en_curso, emitido = tres_estudios
    respuesta = cliente_http.get(URL, {"listos": "1"})
    assert filas(respuesta) == [listo.pk]
    html = respuesta.content.decode()
    assert re.search(r'name="listos" value="1"[^>]*checked', html)


def test_filtro_listos_se_conserva_al_paginar(cliente_http, estudio_de, completar):
    for _ in range(21):
        completar(estudio_de("CL-"))
    html = cliente_http.get(URL, {"listos": "1", "q": "Muestra"}).content.decode()
    assert "?q=Muestra&amp;listos=1&page=2" in html
    segunda = cliente_http.get(URL, {"listos": "1", "q": "Muestra", "page": 2})
    assert len(filas(segunda)) == 1


def test_menu_e_inicio_enlazan_informes(cliente_http):
    inicio = cliente_http.get(reverse("inicio")).content.decode()
    assert inicio.count(f'href="{URL}"') >= 2  # menú y acceso rápido
    assert "Informes" in inicio
    listado = cliente_http.get(URL).content.decode()
    assert re.search(rf'href="{URL}"[^>]*aria-current="page"', listado)


def test_listado_requiere_sesion(db):
    respuesta = Client().get(URL)
    assert respuesta.status_code == 302
    assert reverse("usuarios:login") in respuesta["Location"]
