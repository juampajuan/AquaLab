import copy
from unittest.mock import patch

import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from usuarios import confirmaciones_administracion as confirmaciones
from usuarios.servicios_administracion import GestionUsuarioError, cambiar_estado_panel, instantanea

pytestmark = pytest.mark.django_db


@pytest.fixture
def request_panel(administrador_panel):
    request = RequestFactory().post("/")
    SessionMiddleware(lambda request: None).process_request(request)
    request.session.create()
    request.user = administrador_panel
    return request


def propuesta(request, usuario, operacion="aprobar", datos=None):
    return confirmaciones.preparar(
        request,
        operacion,
        usuario.pk,
        usuario.version_administrativa,
        datos or {},
        instantanea(usuario),
    )


def test_confirmar_y_consumir(
    request_panel, usuario_pendiente, django_capture_on_commit_callbacks, mailoutbox
):
    borrador = propuesta(request_panel, usuario_pendiente)
    with django_capture_on_commit_callbacks(execute=True):
        assert confirmaciones.confirmar(request_panel, borrador["token"])
    assert len(mailoutbox) == 1
    with pytest.raises(signing.BadSignature):
        confirmaciones.confirmar(request_panel, borrador["token"])


def test_cancelar_sin_cambios(request_panel, usuario_pendiente, mailoutbox):
    antes = instantanea(usuario_pendiente)
    borrador = propuesta(request_panel, usuario_pendiente)
    assert not confirmaciones.confirmar(request_panel, borrador["token"], cancelar=True)
    usuario_pendiente.refresh_from_db()
    assert instantanea(usuario_pendiente) == antes
    assert not mailoutbox
    with pytest.raises(signing.BadSignature):
        confirmaciones.verificar(request_panel, borrador["token"])


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("operacion", "rechazar"),
        ("usuario_id", 999),
        ("version", 9),
        ("datos", {"activa": True}),
        ("original", {}),
    ],
)
def test_digest_detecta_manipulacion(request_panel, usuario_pendiente, campo, valor):
    borrador = propuesta(request_panel, usuario_pendiente)
    copia = copy.deepcopy(request_panel.session[confirmaciones.CLAVE_SESION])
    copia[borrador["clave"]][campo] = valor
    request_panel.session[confirmaciones.CLAVE_SESION] = copia
    with pytest.raises(signing.BadSignature):
        confirmaciones.verificar(request_panel, borrador["token"])


def test_firma_identidad_sesion_y_expiracion(request_panel, usuario_pendiente, administrador):
    borrador = propuesta(request_panel, usuario_pendiente)
    token = borrador["token"]
    with pytest.raises(signing.BadSignature):
        confirmaciones.verificar(request_panel, token + "alterado")
    with patch("django.core.signing.time.time", return_value=10**11):
        with pytest.raises(signing.SignatureExpired):
            confirmaciones.verificar(request_panel, token)
    datos = signing.loads(token, salt=confirmaciones.SALT_CONFIRMACION)
    assert request_panel.session.session_key not in str(datos)
    assert "password" not in str(datos)
    request_panel.session.cycle_key()
    with pytest.raises(signing.BadSignature):
        confirmaciones.verificar(request_panel, token)
    request_panel.user = administrador
    with pytest.raises(PermissionDenied):
        confirmaciones.verificar(request_panel, token)


def test_revocacion_no_es_eludida_por_firma(request_panel, usuario_pendiente):
    borrador = propuesta(request_panel, usuario_pendiente)
    request_panel.user.groups.clear()
    with pytest.raises(PermissionDenied):
        confirmaciones.confirmar(request_panel, borrador["token"])
    usuario_pendiente.refresh_from_db()
    assert not usuario_pendiente.aprobada


def test_limite_20_y_purga_ttl(request_panel, usuario_pendiente):
    with patch.object(confirmaciones.time, "time", return_value=1000):
        for _ in range(20):
            propuesta(request_panel, usuario_pendiente)
        with pytest.raises(signing.BadSignature, match="demasiadas"):
            propuesta(request_panel, usuario_pendiente)
    with patch.object(confirmaciones.time, "time", return_value=4601):
        assert not confirmaciones.pendientes(request_panel)
        propuesta(request_panel, usuario_pendiente)


def test_aba_rechaza_confirmacion(request_panel, usuario_aprobado):
    borrador = propuesta(request_panel, usuario_aprobado, "estado", {"activa": False})
    cambiar_estado_panel(request_panel, usuario_aprobado.pk, False, 1)
    cambiar_estado_panel(request_panel, usuario_aprobado.pk, True, 2)
    with pytest.raises(GestionUsuarioError, match="cambió"):
        confirmaciones.confirmar(request_panel, borrador["token"])


def test_propuesta_cerrada_no_almacena_secretos(request_panel, usuario_pendiente):
    with pytest.raises(signing.BadSignature):
        propuesta(request_panel, usuario_pendiente, datos={"password": "secreto"})
    assert not request_panel.session.get(confirmaciones.CLAVE_SESION)


def test_contexto_admin_no_intercambia_operaciones(request_panel, usuario_pendiente):
    token = confirmaciones.firmar_ficha(request_panel, instantanea(usuario_pendiente))
    with pytest.raises(signing.BadSignature):
        confirmaciones.leer_ficha(request_panel, token, operacion="rechazar")


def test_actor_distinto_aunque_autorizado(
    request_panel, usuario_pendiente, django_user_model, grupo_administradores
):
    borrador = propuesta(request_panel, usuario_pendiente)
    otro = django_user_model.objects.create_user(email="otro.panel@lab.com")
    otro.groups.add(grupo_administradores)
    request_panel.user = otro
    with pytest.raises(signing.BadSignature):
        confirmaciones.verificar(request_panel, borrador["token"])
