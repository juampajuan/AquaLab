import pytest
from django.contrib.messages import get_messages
from django.db import DatabaseError
from django.urls import reverse

from estudios.models import Estudio, PruebaEstudio

pytestmark = pytest.mark.django_db


def url_detalle(estudio):
    return reverse("estudios:detalle", args=[estudio.pk])


def url_agregar(estudio):
    return reverse("estudios:agregar_prueba", args=[estudio.pk])


def textos(respuesta):
    return [str(m) for m in get_messages(respuesta.wsgi_request)]


def test_detalle_muestra_cabecera_pruebas_y_accion_agregar(cliente_http, estudio):
    r = cliente_http.get(url_detalle(estudio))
    html = r.content.decode()
    assert r.status_code == 200
    for texto in (f"Estudio {estudio.pk}", "PI 200001", "Tipo de test", "Pendiente de análisis"):
        assert texto in html
    assert "TEST-A" in html and "TEST-B" in html
    assert url_agregar(estudio) in html


def test_exito_creacion_enlaza_al_detalle(cliente_http, muestra, tipo):
    r = cliente_http.post("/estudios/crear/", {"muestra": muestra.pk, "tipo": tipo.pk})
    token = cliente_http.get(r.url).context["borrador"]["token"]
    r = cliente_http.post(
        "/estudios/crear/confirmar/", {"accion": "confirmar", "token": token}, follow=True
    )
    assert f'href="{url_detalle(Estudio.objects.get())}"' in r.content.decode()


def test_agregar_ofrece_solo_pruebas_no_asignadas(cliente_http, estudio, prueba_extra):
    r = cliente_http.get(url_agregar(estudio))
    assert r.status_code == 200
    opciones = set(r.context["form"].fields["prueba"].queryset.values_list("codigo", flat=True))
    assert opciones == {"TEST-C"}


def test_revisar_muestra_confirmacion_sin_guardar(cliente_http, estudio, prueba_extra):
    r = cliente_http.post(url_agregar(estudio), {"accion": "revisar", "prueba": prueba_extra.pk})
    html = r.content.decode()
    assert r.status_code == 200
    assert "Se agregará la prueba TEST-C · Prueba de test C" in html
    assert f'href="{url_detalle(estudio)}"' in html
    assert estudio.pruebas_asignadas.count() == 2


def test_confirmar_agrega_prueba_una_vez(cliente_http, estudio, prueba_extra):
    r = cliente_http.post(url_agregar(estudio), {"accion": "confirmar", "prueba": prueba_extra.pk})
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    assert textos(r) == [f"Prueba TEST-C · Prueba de test C agregada al estudio {estudio.pk}."]
    assert estudio.pruebas_asignadas.filter(prueba=prueba_extra).count() == 1


def test_agregar_sin_pruebas_disponibles_informa(cliente_http, estudio):
    r = cliente_http.get(url_agregar(estudio))
    html = r.content.decode()
    assert "No hay pruebas disponibles para agregar: todas ya forman parte del estudio." in html
    assert 'name="prueba"' not in html


def test_error_de_base_al_agregar_no_cambia_estudio(
    cliente_http, estudio, prueba_extra, monkeypatch
):
    def fallar(*args, **kwargs):
        raise DatabaseError

    monkeypatch.setattr("estudios.servicios.agregar_prueba", fallar)
    r = cliente_http.post(url_agregar(estudio), {"accion": "confirmar", "prueba": prueba_extra.pk})
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    assert textos(r) == ["No se pudo agregar la prueba. Intentá nuevamente."]
    assert not PruebaEstudio.objects.filter(prueba=prueba_extra).exists()


@pytest.mark.parametrize(
    ("metodo", "ruta"),
    [
        ("get", "estudios:detalle"),
        ("get", "estudios:agregar_prueba"),
        ("post", "estudios:agregar_prueba"),
    ],
)
def test_vistas_agregar_prueba_requieren_sesion(client, estudio, prueba_extra, metodo, ruta):
    url = reverse(ruta, args=[estudio.pk])
    r = getattr(client, metodo)(url, {"accion": "confirmar", "prueba": prueba_extra.pk})
    assert r.status_code == 302 and "/usuarios/" in r.url
    assert estudio.pruebas_asignadas.count() == 2


def test_revisar_prueba_ya_asignada_da_error_en_campo(cliente_http, estudio, pruebas):
    r = cliente_http.post(url_agregar(estudio), {"accion": "revisar", "prueba": pruebas[0].pk})
    assert r.status_code == 200 and r.context["form"].errors["prueba"]


def test_reenvio_confirmar_agregar_no_duplica(cliente_http, estudio, prueba_extra):
    datos = {"accion": "confirmar", "prueba": prueba_extra.pk}
    cliente_http.post(url_agregar(estudio), datos)
    r = cliente_http.post(url_agregar(estudio), datos)
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    mensaje = list(get_messages(r.wsgi_request))[-1]
    assert str(mensaje) == "La prueba TEST-C ya forma parte del estudio." and mensaje.tags == "info"
    assert estudio.pruebas_asignadas.filter(prueba=prueba_extra).count() == 1


@pytest.mark.parametrize("accion", ["revisar", "confirmar"])
def test_agregar_prueba_inexistente_rechazada(cliente_http, estudio, accion):
    r = cliente_http.post(url_agregar(estudio), {"accion": accion, "prueba": 999999})
    assert r.status_code == 200 and r.context["form"].errors["prueba"]
    assert estudio.pruebas_asignadas.count() == 2


def test_vistas_estudio_no_modificable_no_ofrecen_agregar(cliente_http, estudio, monkeypatch):
    monkeypatch.setattr(Estudio, "admite_modificaciones", property(lambda self: False))
    r = cliente_http.get(url_agregar(estudio))
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    assert textos(r) == ["Este estudio ya no admite cambios en sus pruebas."]
    html = cliente_http.get(url_detalle(estudio)).content.decode()
    assert "Este estudio ya no admite cambios en sus pruebas." in html
    assert url_agregar(estudio) not in html


def test_estudio_inexistente_responde_404(cliente_http):
    assert cliente_http.get(reverse("estudios:detalle", args=[999999])).status_code == 404
    assert cliente_http.get(reverse("estudios:agregar_prueba", args=[999999])).status_code == 404
