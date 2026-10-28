from unittest import mock

import pytest
from django.contrib.messages import get_messages
from django.db import DatabaseError
from django.test import Client
from django.urls import reverse

from estudios.models import EstadoEstudio, Estudio, PruebaEstudio

pytestmark = pytest.mark.django_db


def url_detalle(estudio):
    return reverse("estudios:detalle", args=[estudio.pk])


def url_agregar(estudio):
    return reverse("estudios:agregar_prueba", args=[estudio.pk])


def mensajes(respuesta):
    return [str(m) for m in get_messages(respuesta.wsgi_request)]


def test_detalle_ofrece_agregar_prueba(cliente_http, estudio):
    r = cliente_http.get(url_detalle(estudio))
    html = r.content.decode()
    assert r.status_code == 200
    assert "TEST-A" in html and "TEST-B" in html
    assert f'href="{url_agregar(estudio)}"' in html


def test_exito_creacion_enlaza_al_detalle(cliente_http, muestra, tipo):
    r = cliente_http.post(reverse("estudios:crear"), {"muestra": muestra.pk, "tipo": tipo.pk})
    token = cliente_http.get(r.url).context["borrador"]["token"]
    r = cliente_http.post(
        reverse("estudios:confirmar"), {"accion": "confirmar", "token": token}, follow=True
    )
    estudio = Estudio.objects.get()
    assert f'<a href="{url_detalle(estudio)}">Estudio {estudio.pk}</a>' in r.content.decode()


def test_agregar_ofrece_solo_pruebas_no_asignadas(cliente_http, estudio, prueba_extra):
    r = cliente_http.get(url_agregar(estudio))
    assert r.status_code == 200
    opciones = list(r.context["form"].fields["prueba"].queryset.values_list("codigo", flat=True))
    assert opciones == ["TEST-C"]
    html = r.content.decode()
    assert "TEST-C · Prueba de test C" in html
    assert "TEST-A" not in html and "TEST-B" not in html


def test_revisar_muestra_confirmacion_sin_guardar(cliente_http, estudio, prueba_extra):
    r = cliente_http.post(url_agregar(estudio), {"accion": "revisar", "prueba": prueba_extra.pk})
    html = r.content.decode()
    assert r.status_code == 200
    assert "Se agregará la prueba" in html
    assert "TEST-C · Prueba de test C" in html
    assert f'href="{url_detalle(estudio)}"' in html
    assert not estudio.pruebas_asignadas.filter(prueba=prueba_extra).exists()


def test_confirmar_agrega_prueba_una_vez(cliente_http, estudio, prueba_extra):
    r = cliente_http.post(url_agregar(estudio), {"accion": "confirmar", "prueba": prueba_extra.pk})
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    assert mensajes(r) == [f"Prueba TEST-C · Prueba de test C agregada al estudio {estudio.pk}."]
    assert estudio.pruebas_asignadas.filter(prueba=prueba_extra).count() == 1


def test_agregar_sin_pruebas_disponibles_informa(cliente_http, estudio):
    r = cliente_http.get(url_agregar(estudio))
    html = r.content.decode()
    assert r.status_code == 200
    assert "No hay pruebas disponibles para agregar: todas ya forman parte del estudio." in html
    assert 'name="prueba"' not in html
    assert f'href="{url_detalle(estudio)}"' in html


def test_error_de_base_al_agregar_no_cambia_estudio(cliente_http, estudio, prueba_extra):
    with mock.patch("estudios.servicios.agregar_prueba", side_effect=DatabaseError):
        r = cliente_http.post(
            url_agregar(estudio), {"accion": "confirmar", "prueba": prueba_extra.pk}
        )
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    assert mensajes(r) == ["No se pudo agregar la prueba. Intentá nuevamente."]
    assert PruebaEstudio.objects.filter(estudio=estudio).count() == 2


@pytest.mark.parametrize(
    ("ruta", "metodo"),
    [("detalle", "get"), ("agregar_prueba", "get"), ("agregar_prueba", "post")],
)
def test_vistas_agregar_prueba_requieren_sesion(estudio, prueba_extra, ruta, metodo):
    url = reverse(f"estudios:{ruta}", args=[estudio.pk])
    r = getattr(Client(), metodo)(url, {"accion": "confirmar", "prueba": prueba_extra.pk})
    assert r.status_code == 302
    assert r.url.startswith(reverse("usuarios:login"))
    assert PruebaEstudio.objects.filter(estudio=estudio).count() == 2


def test_revisar_prueba_ya_asignada_da_error_en_campo(cliente_http, estudio, pruebas, prueba_extra):
    r = cliente_http.post(url_agregar(estudio), {"accion": "revisar", "prueba": pruebas[0].pk})
    assert r.status_code == 200
    assert r.context["form"].errors["prueba"]
    assert "is-invalid" in r.content.decode()


def test_reenvio_confirmar_agregar_no_duplica(cliente_http, estudio, prueba_extra):
    datos = {"accion": "confirmar", "prueba": prueba_extra.pk}
    cliente_http.post(url_agregar(estudio), datos, follow=True)
    r = cliente_http.post(url_agregar(estudio), datos)
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    [mensaje] = list(get_messages(r.wsgi_request))
    assert str(mensaje) == "La prueba TEST-C ya forma parte del estudio."
    assert mensaje.level_tag == "info"
    assert estudio.pruebas_asignadas.filter(prueba=prueba_extra).count() == 1


@pytest.mark.parametrize("accion", ["revisar", "confirmar"])
def test_agregar_prueba_inexistente_rechazada(cliente_http, estudio, prueba_extra, accion):
    r = cliente_http.post(url_agregar(estudio), {"accion": accion, "prueba": 999999})
    assert r.status_code == 200
    assert r.context["form"].errors["prueba"]
    assert PruebaEstudio.objects.filter(estudio=estudio).count() == 2


def test_vistas_estudio_no_modificable_no_ofrecen_agregar(cliente_http, estudio, prueba_extra):
    Estudio.objects.filter(pk=estudio.pk).update(estado=EstadoEstudio.EN_PROCESO)
    r = cliente_http.get(url_agregar(estudio))
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    assert mensajes(r) == ["Este estudio ya no admite cambios en sus pruebas."]
    html = cliente_http.get(url_detalle(estudio)).content.decode()
    assert "Este estudio ya no admite cambios en sus pruebas." in html
    assert url_agregar(estudio) not in html


def test_estudio_inexistente_responde_404(cliente_http):
    for ruta in ("detalle", "agregar_prueba"):
        assert cliente_http.get(reverse(f"estudios:{ruta}", args=[999999])).status_code == 404
