from unittest import mock

import pytest
from django.contrib.messages import get_messages
from django.db import DatabaseError
from django.test import Client
from django.urls import reverse

from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Estudio, PruebaEstudio

pytestmark = pytest.mark.django_db


def url_detalle(estudio):
    return reverse("estudios:detalle", args=[estudio.pk])


def url_quitar(estudio, asignacion):
    return reverse("estudios:quitar_prueba", args=[estudio.pk, asignacion.pk])


def mensajes(respuesta):
    return [str(m) for m in get_messages(respuesta.wsgi_request)]


def test_detalle_ofrece_quitar_en_pruebas_quitables(cliente_http, estudio):
    html = cliente_http.get(url_detalle(estudio)).content.decode()
    for asignacion in estudio.pruebas_asignadas.all():
        assert f'href="{url_quitar(estudio, asignacion)}"' in html


def test_quitar_get_muestra_confirmacion_sin_borrar(cliente_http, estudio, asignacion):
    r = cliente_http.get(url_quitar(estudio, asignacion))
    html = r.content.decode()
    assert r.status_code == 200
    assert f"Se quitará la prueba TEST-A · Prueba de test A del estudio {estudio.pk}" in html
    assert f'href="{url_detalle(estudio)}"' in html
    assert PruebaEstudio.objects.filter(pk=asignacion.pk).exists()


def test_confirmar_quita_prueba(cliente_http, estudio, asignacion):
    r = cliente_http.post(url_quitar(estudio, asignacion))
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    assert mensajes(r) == [f"Prueba TEST-A · Prueba de test A quitada del estudio {estudio.pk}."]
    assert not PruebaEstudio.objects.filter(pk=asignacion.pk).exists()
    agregar = cliente_http.get(reverse("estudios:agregar_prueba", args=[estudio.pk]))
    assert "TEST-A · Prueba de test A" in agregar.content.decode()


def test_error_de_base_al_quitar_no_cambia_estudio(cliente_http, estudio, asignacion):
    with mock.patch("estudios.servicios.quitar_prueba", side_effect=DatabaseError):
        r = cliente_http.post(url_quitar(estudio, asignacion))
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    assert mensajes(r) == ["No se pudo quitar la prueba. Intentá nuevamente."]
    assert PruebaEstudio.objects.filter(pk=asignacion.pk).exists()


@pytest.mark.parametrize("metodo", ["get", "post"])
def test_vistas_quitar_prueba_requieren_sesion(estudio, asignacion, metodo):
    r = getattr(Client(), metodo)(url_quitar(estudio, asignacion))
    assert r.status_code == 302
    assert r.url.startswith(reverse("usuarios:login"))
    assert PruebaEstudio.objects.filter(pk=asignacion.pk).exists()


def test_reenvio_confirmar_quitar_informa_ya_quitada(cliente_http, estudio, asignacion):
    cliente_http.post(url_quitar(estudio, asignacion), follow=True)
    r = cliente_http.post(url_quitar(estudio, asignacion))
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    [mensaje] = list(get_messages(r.wsgi_request))
    assert str(mensaje) == "La prueba ya no forma parte del estudio."
    assert mensaje.level_tag == "info"


def test_detalle_no_ofrece_quitar_ultima_prueba(cliente_http, estudio, asignacion):
    estudio.pruebas_asignadas.exclude(pk=asignacion.pk).delete()
    html = cliente_http.get(url_detalle(estudio)).content.decode()
    assert url_quitar(estudio, asignacion) not in html
    assert "El estudio debe conservar al menos una prueba." in html
    r = cliente_http.get(url_quitar(estudio, asignacion))
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    assert mensajes(r) == ["El estudio debe conservar al menos una prueba."]


def test_detalle_no_ofrece_quitar_prueba_con_mediciones(cliente_http, estudio, asignacion):
    PruebaEstudio.objects.filter(pk=asignacion.pk).update(estado=EstadoPruebaEstudio.CARGADA)
    otra = estudio.pruebas_asignadas.get(prueba__codigo="TEST-B")
    html = cliente_http.get(url_detalle(estudio)).content.decode()
    assert url_quitar(estudio, asignacion) not in html
    assert url_quitar(estudio, otra) in html
    r = cliente_http.get(url_quitar(estudio, asignacion))
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    assert mensajes(r) == ["La prueba tiene mediciones o resultados cargados y no se puede quitar."]


def test_vistas_estudio_no_modificable_no_ofrecen_quitar(cliente_http, estudio, asignacion):
    Estudio.objects.filter(pk=estudio.pk).update(estado=EstadoEstudio.EN_PROCESO)
    r = cliente_http.get(url_quitar(estudio, asignacion))
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    assert mensajes(r) == ["Este estudio ya no admite cambios en sus pruebas."]
    html = cliente_http.get(url_detalle(estudio)).content.decode()
    assert url_quitar(estudio, asignacion) not in html
    assert ">Quitar<" not in html


@pytest.mark.parametrize("metodo", ["get", "post"])
def test_quitar_estudio_inexistente_responde_404(cliente_http, asignacion, metodo):
    url = reverse("estudios:quitar_prueba", args=[999999, asignacion.pk])
    assert getattr(cliente_http, metodo)(url).status_code == 404


@pytest.mark.parametrize("metodo", ["get", "post"])
def test_quitar_asignacion_de_otro_estudio_rechazada(
    cliente_http, estudio, datos, empleado, metodo
):
    import uuid

    from estudios.servicios import crear_estudio

    otro = crear_estudio({**datos, "clave": str(uuid.uuid4())}, empleado)
    ajena = otro.pruebas_asignadas.first()
    r = getattr(cliente_http, metodo)(url_quitar(estudio, ajena))
    assert r.status_code == 302 and r.url == url_detalle(estudio)
    assert mensajes(r) == ["La prueba ya no forma parte del estudio."]
    assert PruebaEstudio.objects.filter(pk=ajena.pk).exists()
