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


def test_listado_solo_muestra_los_listos(cliente_http, tres_estudios):
    """SCRUM-82: sin iniciar, en proceso o con informe emitido no se listan."""
    listo, en_curso, emitido = tres_estudios
    respuesta = cliente_http.get(URL)
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "Informes por emitir" in html
    assert filas(respuesta) == [listo.pk]
    assert reverse("informes:vista_previa", args=[listo.pk]) in html
    assert "Generar informe</a>" in html
    assert 'name="listos"' not in html


def test_listado_ordenado_y_paginado(cliente_http, estudio_de, completar):
    estudios = [estudio_de("CL-") for _ in range(21)]
    for estudio in estudios:
        completar(estudio)
    pks = sorted((e.pk for e in estudios), reverse=True)
    primera = cliente_http.get(URL)
    assert filas(primera) == pks[:20]
    segunda = cliente_http.get(URL, {"page": 2})
    assert filas(segunda) == pks[20:]


@pytest.mark.parametrize("busqueda", ["200001", "estudio", "Cliente de test", "tipo"])
def test_busqueda_por_numero_pi_cliente_y_tipo(cliente_http, tres_estudios, busqueda):
    listo, en_curso, emitido = tres_estudios
    if busqueda == "estudio":
        busqueda = str(listo.pk)
    elif busqueda == "tipo":
        busqueda = listo.tipo_nombre_snapshot
    respuesta = cliente_http.get(URL, {"q": busqueda})
    assert filas(respuesta) == [listo.pk]


def test_busqueda_no_encuentra_los_no_listos(cliente_http, tres_estudios):
    assert filas(cliente_http.get(URL, {"q": "200002"})) == []
    assert filas(cliente_http.get(URL, {"q": "Aguas del Sur"})) == []


def test_busqueda_sin_resultados(cliente_http, tres_estudios):
    respuesta = cliente_http.get(URL, {"q": "zzz"})
    assert filas(respuesta) == []
    assert "No hay informes por emitir" in respuesta.content.decode()


def test_busqueda_demasiado_larga(cliente_http, tres_estudios):
    respuesta = cliente_http.get(URL, {"q": "a" * 101})
    assert "Ingresá como máximo 100 caracteres para buscar." in respuesta.content.decode()


def test_busqueda_se_conserva_al_paginar(cliente_http, estudio_de, completar):
    for _ in range(21):
        completar(estudio_de("CL-"))
    html = cliente_http.get(URL, {"q": "Muestra"}).content.decode()
    assert "?q=Muestra&page=2" in html
    segunda = cliente_http.get(URL, {"q": "Muestra", "page": 2})
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


def test_generar_informe_abre_la_vista_previa(cliente_http, estudio_de, completar):
    estudio = estudio_de("CL-")
    completar(estudio)
    html = cliente_http.get(URL).content.decode()
    enlace = re.search(r'href="([^"]+)"[^>]*>Generar informe</a>', html).group(1)
    assert enlace == reverse("informes:vista_previa", args=[estudio.pk]) + "?desde=listos"
    assert cliente_http.get(enlace).status_code == 200
