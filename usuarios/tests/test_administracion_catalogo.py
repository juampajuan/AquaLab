import pytest
from django.urls import reverse

from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


def test_catalogo_datos_busqueda_y_unidad(cliente_panel):
    prueba = Prueba.objects.create(codigo="ABC", nombre="Alcalinidad", unidad="--", activa=False)
    Prueba.objects.create(codigo="OTR", nombre="Otra", unidad="mg/L")
    url = reverse("administracion:pruebas")
    for busqueda in ["abc", " CALIN "]:
        respuesta = cliente_panel.get(url, {"q": busqueda})
        html = respuesta.content.decode()
        assert list(respuesta.context["page_obj"]) == [prueba]
        for texto in [
            "ABC",
            "Alcalinidad",
            "Directo",
            "Sin unidad",
            "Inactiva",
            reverse("admin:pruebas_prueba_change", args=[prueba.pk]),
        ]:
            assert texto in html
    assert len(cliente_panel.get(url, {"q": " "}).context["page_obj"]) == 2
    html = cliente_panel.get(url, {"q": "ausente"}).content.decode()
    assert "No hay pruebas" in html and "Limpiar" in html


def test_paginacion_y_busqueda_conservada(cliente_panel):
    Prueba.objects.bulk_create(
        [Prueba(codigo=f"COD{i:02}", nombre=f"Prueba {i}") for i in range(21)]
    )
    url = reverse("administracion:pruebas")
    respuesta = cliente_panel.get(url, {"q": "Prueba"})
    assert len(respuesta.context["page_obj"]) == 20
    from html import unescape

    assert "q=Prueba&page=2" in unescape(respuesta.content.decode())
    ultima = cliente_panel.get(url, {"q": "Prueba", "page": 2})
    assert [p.codigo for p in ultima.context["page_obj"]] == ["COD20"]


def test_catalogo_vacio_y_solo_lectura(cliente_panel):
    url = reverse("administracion:pruebas")
    assert "No hay pruebas" in cliente_panel.get(url).content.decode()
    assert cliente_panel.post(url, {"codigo": "INY"}).status_code == 405
    assert not Prueba.objects.exists()
