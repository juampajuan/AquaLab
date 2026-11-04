import pytest
from django.urls import reverse

from usuarios.models import Usuario

pytestmark = pytest.mark.django_db


@pytest.fixture
def cliente_panel(client, administrador_panel):
    client.force_login(administrador_panel)
    return client


def revision(cliente, nombre, usuario):
    return cliente.get(reverse("administracion:" + nombre, args=[usuario.pk]))


def resolver(cliente, nombre, usuario, *, accion="confirmar"):
    respuesta = revision(cliente, nombre, usuario)
    return cliente.post(
        reverse("administracion:" + nombre, args=[usuario.pk]),
        {"accion": accion, "token": respuesta.context["token"]},
        follow=True,
    )


def test_listado_solo_pendientes(cliente_panel, usuario_pendiente, usuario_desactivado):
    respuesta = cliente_panel.get(reverse("administracion:solicitudes"))
    html = respuesta.content.decode()
    assert usuario_pendiente.email in html and usuario_desactivado.email not in html
    assert "Aprobar" in html and "Rechazar" in html


@pytest.mark.parametrize("nombre", ["aprobar", "rechazar"])
def test_resolucion_confirmada(
    cliente_panel, usuario_pendiente, nombre, django_capture_on_commit_callbacks, mailoutbox
):
    with django_capture_on_commit_callbacks(execute=True):
        respuesta = resolver(cliente_panel, nombre, usuario_pendiente)
    assert respuesta.status_code == 200
    assert len(mailoutbox) == 1
    if nombre == "aprobar":
        usuario_pendiente.refresh_from_db()
        assert usuario_pendiente.is_active and usuario_pendiente.aprobada
        assert "/usuarios/login/" in mailoutbox[0].body
    else:
        assert not Usuario.objects.filter(email=usuario_pendiente.email).exists()
        Usuario.objects.create_user(email=usuario_pendiente.email)


def test_revision_cancelacion_y_reenvio(cliente_panel, usuario_pendiente, mailoutbox):
    previa = revision(cliente_panel, "rechazar", usuario_pendiente)
    assert usuario_pendiente.email in previa.content.decode()
    token = previa.context["token"]
    url = reverse("administracion:rechazar", args=[usuario_pendiente.pk])
    cliente_panel.post(url, {"accion": "cancelar", "token": token})
    cliente_panel.post(url, {"accion": "confirmar", "token": token})
    usuario_pendiente.refresh_from_db()
    assert not usuario_pendiente.aprobada and not mailoutbox


@pytest.mark.parametrize("relacion", ["firma", "muestra"])
def test_historico_impedido_aprobacion_posterior(
    cliente_panel,
    usuario_pendiente,
    historial_usuario,
    relacion,
    django_capture_on_commit_callbacks,
    mailoutbox,
):
    referencia = historial_usuario(usuario_pendiente, relacion)
    with django_capture_on_commit_callbacks(execute=True):
        respuesta = resolver(cliente_panel, "rechazar", usuario_pendiente)
    assert "No se puede rechazar" in respuesta.content.decode()
    usuario_pendiente.refresh_from_db()
    referencia.refresh_from_db()
    assert not usuario_pendiente.is_active and usuario_pendiente.version_administrativa == 1
    assert not mailoutbox
    with django_capture_on_commit_callbacks(execute=True):
        resolver(cliente_panel, "aprobar", usuario_pendiente)
    referencia.refresh_from_db()
    assert len(mailoutbox) == 1


def test_objetivo_ausente_y_resuelto(cliente_panel, usuario_aprobado, usuario_pendiente):
    assert (
        revision(cliente_panel, "aprobar", type("Ausente", (), {"pk": 999999})()).status_code == 404
    )
    respuesta = revision(cliente_panel, "rechazar", usuario_aprobado)
    assert respuesta.status_code == 302
    previa = revision(cliente_panel, "aprobar", usuario_pendiente)
    pk = usuario_pendiente.pk
    usuario_pendiente.delete()
    respuesta = cliente_panel.post(
        reverse("administracion:aprobar", args=[pk]),
        {"accion": "confirmar", "token": previa.context["token"]},
        follow=True,
    )
    assert "no está disponible" in respuesta.content.decode()


def test_solicitudes_orden_y_paginacion(cliente_panel, django_user_model):
    cuentas = [
        django_user_model.objects.create_user(email=f"pendiente{i}@lab.com", is_active=False)
        for i in range(21)
    ]
    respuesta = cliente_panel.get(reverse("administracion:solicitudes"))
    assert len(respuesta.context["page_obj"]) == 20
    assert respuesta.context["page_obj"][0].pk == cuentas[-1].pk
    respuesta = cliente_panel.get(reverse("administracion:solicitudes"), {"page": 2})
    assert len(respuesta.context["page_obj"]) == 1


def test_confirmacion_alterada_caducada_y_objetivo_distinto(
    cliente_panel, usuario_pendiente, usuario_aprobado
):
    import time
    from unittest.mock import patch

    previa = revision(cliente_panel, "aprobar", usuario_pendiente)
    token = previa.context["token"]
    datos = {"accion": "confirmar", "token": token}
    cliente_panel.post(reverse("administracion:aprobar", args=[usuario_aprobado.pk]), datos)
    url = reverse("administracion:aprobar", args=[usuario_pendiente.pk])
    cliente_panel.post(url, {**datos, "token": token + "alterado"})
    with patch("django.core.signing.time.time", return_value=time.time() + 3601):
        respuesta = cliente_panel.post(url, datos, follow=True)
    assert "venció" in respuesta.content.decode()
    usuario_pendiente.refresh_from_db()
    assert not usuario_pendiente.aprobada


def test_solicitud_resuelta_entre_revision_y_confirmacion(
    cliente_panel, usuario_pendiente, django_capture_on_commit_callbacks, mailoutbox
):
    previa = revision(cliente_panel, "aprobar", usuario_pendiente)
    with django_capture_on_commit_callbacks(execute=True):
        resolver(cliente_panel, "aprobar", usuario_pendiente)
        respuesta = cliente_panel.post(
            reverse("administracion:aprobar", args=[usuario_pendiente.pk]),
            {"accion": "confirmar", "token": previa.context["token"]},
            follow=True,
        )
    assert len(mailoutbox) == 1
    assert "pendiente" in respuesta.content.decode()
