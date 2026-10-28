import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import signing
from django.test import RequestFactory

from estudios import confirmaciones_tipos as tokens

pytestmark = pytest.mark.django_db


@pytest.fixture
def peticion(gestor):
    req = RequestFactory().get("/")
    SessionMiddleware(lambda r: None).process_request(req)
    req.user = gestor
    return req


def test_fases_y_sesion(peticion):
    contexto = tokens.crear_contexto(peticion, "editar", 1, 2)
    assert tokens.leer_contexto(peticion, contexto, "editar", 1)["version"] == 2
    with pytest.raises(signing.BadSignature):
        tokens.leer_contexto(peticion, contexto, "editar", 2)
    with pytest.raises(signing.BadSignature):
        tokens.verificar(peticion, contexto)


def test_borradores_aislados_digest_cancelacion(peticion):
    a = tokens.preparar(peticion, "crear", None, None, {"nombre": "A", "prueba_ids": [2, 1, 2]}, {})
    b = tokens.preparar(peticion, "crear", None, None, {"nombre": "B", "prueba_ids": [1]}, {})
    assert a["clave"] != b["clave"]
    assert tokens.verificar(peticion, a["token"])["datos"]["prueba_ids"] == [1, 2]
    tokens.descartar(peticion, a["clave"])
    with pytest.raises(signing.BadSignature):
        tokens.verificar(peticion, a["token"])
    assert tokens.verificar(peticion, b["token"])["datos"]["nombre"] == "B"


def test_limite_y_purga(peticion, monkeypatch):
    for _ in range(20):
        tokens.preparar(peticion, "crear", None, None, {}, {})
    with pytest.raises(signing.BadSignature):
        tokens.preparar(peticion, "crear", None, None, {}, {})
    monkeypatch.setattr(tokens.time, "time", lambda: 9999999999)
    tokens.preparar(peticion, "crear", None, None, {}, {})
    assert len(tokens.pendientes(peticion)) == 1


def test_manipulacion_y_vencimiento(peticion, monkeypatch):
    borrador = tokens.preparar(peticion, "crear", None, None, {"nombre": "Original"}, {})
    with pytest.raises(signing.BadSignature):
        tokens.verificar(peticion, borrador["token"] + "x")
    copia = dict(peticion.session[tokens.CLAVE_SESION])
    copia[borrador["clave"]]["datos"]["nombre"] = "Alterado"
    peticion.session[tokens.CLAVE_SESION] = copia
    with pytest.raises(signing.BadSignature):
        tokens.verificar(peticion, borrador["token"])
    contexto = tokens.crear_contexto(peticion, "crear")
    monkeypatch.setattr(signing.time, "time", lambda: 9999999999)
    with pytest.raises(signing.SignatureExpired):
        tokens.leer_contexto(peticion, contexto, "crear")


@pytest.mark.parametrize(
    "campo,valor", [("operacion", "eliminar"), ("tipo_id", 2), ("version", 99)]
)
def test_token_no_admite_cambio_contexto(peticion, campo, valor):
    borrador = tokens.preparar(peticion, "editar", 1, 1, {"nombre": "A"}, {})
    peticion.session[tokens.CLAVE_SESION][borrador["clave"]][campo] = valor
    with pytest.raises(signing.BadSignature):
        tokens.verificar(peticion, borrador["token"])


def test_otra_sesion_usuario_y_fase(peticion, django_user_model):
    borrador = tokens.preparar(peticion, "crear", None, None, {}, {})
    with pytest.raises(signing.BadSignature):
        tokens.leer_contexto(peticion, borrador["token"], "crear")
    peticion.session.cycle_key()
    with pytest.raises(signing.BadSignature):
        tokens.verificar(peticion, borrador["token"])
    peticion.user = django_user_model.objects.create_user(
        email="otro@ejemplo.com", password="Clave-12345"
    )
    with pytest.raises(signing.BadSignature):
        tokens.verificar(peticion, borrador["token"])


@pytest.mark.parametrize("operacion", ["desactivar", "reactivar", "eliminar"])
def test_retiro_no_permite_cambiar_accion_y_cancelado(peticion, operacion):
    borrador = tokens.preparar(peticion, operacion, 1, 1, {}, {})
    assert tokens.verificar(peticion, borrador["token"])["operacion"] == operacion
    tokens.descartar(peticion, borrador["clave"])
    with pytest.raises(signing.BadSignature):
        tokens.verificar(peticion, borrador["token"])


def test_repreparar_invalida_solo_borrador_anterior(peticion):
    a = tokens.preparar(peticion, "crear", None, None, {"nombre": "A"}, {})
    b = tokens.preparar(peticion, "crear", None, None, {"nombre": "B"}, {})
    c = tokens.preparar(peticion, "crear", None, None, {"nombre": "C"}, {}, anterior=a["clave"])
    with pytest.raises(signing.BadSignature):
        tokens.verificar(peticion, a["token"])
    assert tokens.verificar(peticion, b["token"])["datos"]["nombre"] == "B"
    assert tokens.verificar(peticion, c["token"])["datos"]["nombre"] == "C"
