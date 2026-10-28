import pytest
from django.db import DatabaseError
from django.test import Client

from estudios.models import Estudio

pytestmark = pytest.mark.django_db
FORM = "/estudios/crear/"
CONF = "/estudios/crear/confirmar/"


def revisar(c, muestra, tipo):
    r = c.post(FORM, {"muestra": muestra.pk, "tipo": tipo.pk})
    assert r.status_code == 302
    return c.get(r.url)


def token(r):
    return r.context["borrador"]["token"]


def test_formulario_resumen_y_exito(cliente_http, muestra, tipo, empleado):
    r = cliente_http.get(FORM)
    assert r.status_code == 200
    assert str(muestra.numero_pi) in r.content.decode()
    r = revisar(cliente_http, muestra, tipo)
    html = r.content.decode()
    assert "Prueba de test A" in html and "Descripción test" in html
    assert not Estudio.objects.exists()
    t = token(r)
    respuesta = cliente_http.post(CONF, {"accion": "confirmar", "token": t}, follow=True)
    e = Estudio.objects.get()
    assert f"Estudio {e.pk}" in respuesta.content.decode()
    assert e.creado_por == empleado
    cliente_http.post(CONF, {"accion": "confirmar", "token": t})
    assert Estudio.objects.count() == 1


def test_volver_cancelar_y_token_viejo(cliente_http, muestra, tipo):
    r = revisar(cliente_http, muestra, tipo)
    borrador = r.context["borrador"]
    clave = borrador["datos"]["clave"]
    r = cliente_http.get(FORM, {"volver": clave})
    assert r.context["form"].initial["muestra"] == muestra.pk
    cliente_http.post(CONF, {"accion": "cancelar", "token": borrador["token"]})
    cliente_http.post(CONF, {"accion": "confirmar", "token": borrador["token"]})
    assert not Estudio.objects.exists()


@pytest.mark.parametrize(
    "cambio", [{"descripcion": "Cambio"}, {"nombre": "Nuevo"}, {"pruebas": []}]
)
def test_conflicto_y_post_viejo(cliente_http, muestra, tipo, pruebas, cambiar_tipo, cambio):
    anterior = token(revisar(cliente_http, muestra, tipo))
    if cambio == {"pruebas": []}:
        cambio = {"pruebas": [pruebas[0].pk]}
    cambiar_tipo(tipo, **cambio)
    r = cliente_http.post(CONF, {"accion": "confirmar", "token": anterior})
    assert r.status_code == 200
    nuevo = token(r)
    assert nuevo != anterior and not Estudio.objects.exists()
    cliente_http.post(CONF, {"accion": "confirmar", "token": anterior})
    assert not Estudio.objects.exists()
    cliente_http.post(CONF, {"accion": "confirmar", "token": nuevo})
    assert Estudio.objects.count() == 1


def test_get_no_mezcla_version(cliente_http, muestra, tipo, cambiar_tipo):
    r = revisar(cliente_http, muestra, tipo)
    clave = r.context["borrador"]["datos"]["clave"]
    viejo = token(r)
    cambiar_tipo(tipo, nombre="Nombre posterior")
    r = cliente_http.get(CONF, {"solicitud": clave})
    assert "Nombre posterior" not in r.content.decode()
    assert token(r) == viejo


@pytest.mark.parametrize("campo", ["muestra", "tipo"])
def test_faltantes(cliente_http, muestra, tipo, campo):
    datos = {"muestra": muestra.pk, "tipo": tipo.pk, campo: ""}
    r = cliente_http.post(FORM, datos)
    assert r.status_code == 200 and campo in r.context["form"].errors
    assert not Estudio.objects.exists()


def test_cliente_inactivo_y_nueva_solicitud(cliente_http, muestra, tipo, cliente_a):
    cliente_a.activo = False
    cliente_a.save()
    for _ in range(2):
        t = token(revisar(cliente_http, muestra, tipo))
        cliente_http.post(CONF, {"accion": "confirmar", "token": t})
    assert Estudio.objects.count() == 2
    cliente_a.refresh_from_db()
    assert not cliente_a.activo


def test_cliente_desactivado_durante_revision(cliente_http, muestra, tipo, cliente_a):
    t = token(revisar(cliente_http, muestra, tipo))
    cliente_a.activo = False
    cliente_a.save()
    cliente_http.post(CONF, {"accion": "confirmar", "token": t})
    assert Estudio.objects.count() == 1


def test_sin_sesion_y_csrf(client, empleado):
    for r in [
        client.get(FORM),
        client.post(FORM, {}),
        client.get(CONF),
        client.post(CONF, {"accion": "confirmar"}),
    ]:
        assert r.status_code == 302 and "/usuarios/login/" in r.url
    c = Client(enforce_csrf_checks=True)
    c.force_login(empleado)
    assert c.post(CONF, {}).status_code == 403


def test_sin_catalogo(cliente_http):
    r = cliente_http.get(FORM)
    assert r.status_code == 200
    assert "No hay tipos" in r.content.decode()


def test_tipo_inactivo_o_vacio(cliente_http, muestra, tipo):
    tipo.activo = False
    tipo.save()
    assert cliente_http.post(FORM, {"muestra": muestra.pk, "tipo": tipo.pk}).status_code == 200
    tipo.activo = True
    tipo.save()
    tipo.pruebas.clear()
    r = cliente_http.post(FORM, {"muestra": muestra.pk, "tipo": tipo.pk})
    assert r.status_code == 200 and not Estudio.objects.exists()


def test_error_db_informa(cliente_http, muestra, tipo, monkeypatch):
    t = token(revisar(cliente_http, muestra, tipo))

    def fallar(*a, **kw):
        raise DatabaseError("falla de test")

    monkeypatch.setattr("estudios.views.crear_estudio", fallar)
    r = cliente_http.post(CONF, {"accion": "confirmar", "token": t})
    assert r.status_code == 200
    assert "No se pudo crear" in r.content.decode() and not Estudio.objects.exists()


@pytest.mark.parametrize("campo", ["muestra", "tipo"])
def test_referencias_inexistentes(cliente_http, muestra, tipo, campo):
    datos = {"muestra": muestra.pk, "tipo": tipo.pk, campo: 999999}
    r = cliente_http.post(FORM, datos)
    assert r.status_code == 200 and campo in r.context["form"].errors
    assert not Estudio.objects.exists()


def test_campos_automaticos_no_suplantables(cliente_http, muestra, tipo, empleado):
    r = cliente_http.post(
        FORM,
        {
            "muestra": muestra.pk,
            "tipo": tipo.pk,
            "creado_por": 999,
            "tipo_nombre_snapshot": "Inyectado",
            "estado": "finalizado",
            "fecha_creacion": "2000-01-01",
            "clave_idempotencia": "elegida-por-cliente",
        },
    )
    t = token(cliente_http.get(r.url))
    cliente_http.post(
        CONF,
        {
            "accion": "confirmar",
            "token": t,
            "tipo_nombre_snapshot": "Inyectado",
            "creado_por": 999,
            "estado": "finalizado",
        },
    )
    e = Estudio.objects.get()
    assert e.creado_por == empleado and e.estado == "pendiente_analisis"
    assert e.tipo_nombre_snapshot == tipo.nombre
    assert e.fecha_creacion.year != 2000


def test_tipo_desactivado_durante_revision(cliente_http, muestra, tipo, cambiar_tipo):
    t = token(revisar(cliente_http, muestra, tipo))
    cambiar_tipo(tipo, activo=False)
    cliente_http.post(CONF, {"accion": "confirmar", "token": t})
    assert not Estudio.objects.exists()


def test_cambios_sucesivos(cliente_http, muestra, tipo, cambiar_tipo):
    a = token(revisar(cliente_http, muestra, tipo))
    cambiar_tipo(tipo, descripcion="Cambio 1")
    b = token(cliente_http.post(CONF, {"accion": "confirmar", "token": a}))
    cambiar_tipo(tipo, descripcion="Cambio 2")
    c = token(cliente_http.post(CONF, {"accion": "confirmar", "token": b}))
    assert not Estudio.objects.exists()
    cliente_http.post(CONF, {"accion": "confirmar", "token": c})
    assert Estudio.objects.get().tipo_descripcion_snapshot == "Cambio 2"


def test_cuenta_desaprobada(client, django_user_model):
    usuario = django_user_model.objects.create_user(
        email="pendiente@ejemplo.com", password="Clave-Valida-123", is_active=False
    )
    client.force_login(usuario)
    r = client.post(FORM, {})
    assert r.status_code == 302 and "/usuarios/login/" in r.url


def test_muestras_vacias(cliente_http):
    r = cliente_http.get(FORM)
    assert "No hay muestras registradas disponibles" in r.content.decode()
    assert not Estudio.objects.exists()
