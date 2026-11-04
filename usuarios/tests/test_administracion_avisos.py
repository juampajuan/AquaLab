from smtplib import SMTPException

import pytest
from django.db import DatabaseError
from django.urls import reverse

from usuarios.models import Usuario

from .test_administracion_solicitudes import resolver, revision

pytestmark = pytest.mark.django_db


def test_reenvio_aprobacion_no_duplica(
    cliente_panel, usuario_pendiente, django_capture_on_commit_callbacks, mailoutbox
):
    previa = revision(cliente_panel, "aprobar", usuario_pendiente)
    datos = {"accion": "confirmar", "token": previa.context["token"]}
    url = reverse("administracion:aprobar", args=[usuario_pendiente.pk])
    with django_capture_on_commit_callbacks(execute=True):
        cliente_panel.post(url, datos)
        cliente_panel.post(url, datos)
    assert len(mailoutbox) == 1


def test_fallo_smtp_conserva_decision(
    cliente_panel, usuario_pendiente, monkeypatch, caplog, django_capture_on_commit_callbacks
):
    from django.core.mail import EmailMultiAlternatives

    def fallar(*args, **kwargs):
        raise SMTPException("SMTP no disponible")

    monkeypatch.setattr(EmailMultiAlternatives, "send", fallar)
    with django_capture_on_commit_callbacks(execute=True):
        resolver(cliente_panel, "aprobar", usuario_pendiente)
    usuario_pendiente.refresh_from_db()
    assert usuario_pendiente.aprobada and usuario_pendiente.is_active
    assert "SMTP" in caplog.text


def test_error_persistencia_no_deja_transicion(
    cliente_panel, usuario_pendiente, monkeypatch, mailoutbox
):
    previa = revision(cliente_panel, "aprobar", usuario_pendiente)
    original = Usuario.save

    def fallar(obj, *args, **kwargs):
        original(obj, *args, **kwargs)
        if obj.pk == usuario_pendiente.pk:
            raise DatabaseError("fallo de persistencia")

    monkeypatch.setattr(Usuario, "save", fallar)
    respuesta = cliente_panel.post(
        reverse("administracion:aprobar", args=[usuario_pendiente.pk]),
        {"accion": "confirmar", "token": previa.context["token"]},
        follow=True,
    )
    usuario_pendiente.refresh_from_db()
    assert not usuario_pendiente.aprobada and usuario_pendiente.version_administrativa == 1
    assert not mailoutbox
    assert "No se pudo guardar" in respuesta.content.decode()
