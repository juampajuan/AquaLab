import pytest
from django.core import signing
from django.test import Client

from estudios import confirmaciones
from estudios.models import Estudio
from estudios.tests.test_registro import CONF, FORM, revisar, token

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("caso", ["firma", "vacio", "otra_sesion", "otro_usuario"])
def test_rechaza_tokens(cliente_http, muestra, tipo, django_user_model, caso):
    t = token(revisar(cliente_http, muestra, tipo))
    c = cliente_http
    if caso == "firma":
        t = t[:-1] + ("A" if t[-1] != "A" else "B")
    elif caso == "vacio":
        t = ""
    else:
        c = Client()
        usuario = cliente_http.session["_auth_user_id"]
        if caso == "otro_usuario":
            usuario = django_user_model.objects.create_user(
                email="otro@ejemplo.com", password="Clave-Valida-123"
            ).pk
        c.force_login(django_user_model.objects.get(pk=usuario))
    c.post(CONF, {"accion": "confirmar", "token": t})
    c.post(CONF, {"accion": "recuperar", "token": t})
    assert not Estudio.objects.exists()


def test_vencido_recupera_misma_solicitud(cliente_http, muestra, tipo, monkeypatch):
    r = revisar(cliente_http, muestra, tipo)
    previo = r.context["borrador"]
    with monkeypatch.context() as m:
        m.setattr(confirmaciones, "TTL", -1)
        r = cliente_http.post(CONF, {"accion": "confirmar", "token": previo["token"]})
        assert r.context["recuperar"] and not Estudio.objects.exists()
        r = cliente_http.post(CONF, {"accion": "recuperar", "token": previo["token"]})
        assert r.context["borrador"]["datos"]["clave"] == previo["datos"]["clave"]
    cliente_http.post(CONF, {"accion": "confirmar", "token": token(r)})
    assert str(Estudio.objects.get().clave_idempotencia) == previo["datos"]["clave"]


def test_recuperar_exito_y_cancelado(cliente_http, muestra, tipo, monkeypatch):
    t = token(revisar(cliente_http, muestra, tipo))
    cliente_http.post(CONF, {"accion": "confirmar", "token": t})
    with monkeypatch.context() as m:
        m.setattr(confirmaciones, "TTL", -1)
        cliente_http.post(CONF, {"accion": "recuperar", "token": t})
    assert Estudio.objects.count() == 1
    t = token(revisar(cliente_http, muestra, tipo))
    cliente_http.post(CONF, {"accion": "cancelar", "token": t})
    cliente_http.post(CONF, {"accion": "recuperar", "token": t})
    cliente_http.post(CONF, {"accion": "confirmar", "token": t})
    assert Estudio.objects.count() == 1


def test_pestanas_independientes(cliente_http, muestra, tipo):
    a = token(revisar(cliente_http, muestra, tipo))
    b = token(revisar(cliente_http, muestra, tipo))
    cliente_http.post(CONF, {"accion": "cancelar", "token": a})
    cliente_http.post(CONF, {"accion": "confirmar", "token": b})
    assert Estudio.objects.count() == 1


def test_payload_firmado_incompleto(cliente_http, muestra, tipo):
    t = token(revisar(cliente_http, muestra, tipo))
    datos = signing.loads(t, salt=confirmaciones.SALT)
    datos.pop("version")
    t = signing.dumps(datos, salt=confirmaciones.SALT)
    cliente_http.post(CONF, {"accion": "confirmar", "token": t})
    assert not Estudio.objects.exists()


def test_editar_invalida_anterior(cliente_http, muestra, tipo):
    r = revisar(cliente_http, muestra, tipo)
    viejo = r.context["borrador"]
    cliente_http.post(
        FORM, {"muestra": muestra.pk, "tipo": tipo.pk, "anterior": viejo["datos"]["clave"]}
    )
    cliente_http.post(CONF, {"accion": "confirmar", "token": viejo["token"]})
    assert not Estudio.objects.exists()
