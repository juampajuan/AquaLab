"""Tests de la US 1.3: avisos por correo del alta de cuentas."""

import logging
from smtplib import SMTPException

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from .conftest import PASSWORD_EXISTENTE

pytestmark = pytest.mark.django_db

URL_LISTADO = "admin:usuarios_usuario_changelist"
ASUNTO_SOLICITUD_NUEVA = "AquaLab: nueva solicitud de cuenta"
ASUNTO_SOLICITUD_RECIBIDA = "AquaLab: recibimos tu solicitud de cuenta"
ASUNTO_APROBACION = "AquaLab: tu cuenta fue aprobada"
ASUNTO_RECHAZO = "AquaLab: tu solicitud de cuenta no fue aprobada"
LOGGER = "usuarios.notificaciones"


def con_asunto(mailoutbox, asunto):
    return [mensaje for mensaje in mailoutbox if mensaje.subject == asunto]


def url_absoluta(ruta):
    return f"http://testserver{ruta}"


def nueva_pendiente(email, first_name="Laura", last_name="Díaz"):
    return get_user_model().objects.create_user(
        email=email,
        password=PASSWORD_EXISTENTE,
        first_name=first_name,
        last_name=last_name,
        is_active=False,
    )


def datos_ficha(usuario, **cambios):
    """Datos completos del formulario de la ficha del usuario en el admin."""
    fecha_registro = timezone.localtime(usuario.date_joined)
    datos = {
        "email": usuario.email,
        "first_name": usuario.first_name,
        "last_name": usuario.last_name,
        "date_joined_0": fecha_registro.strftime("%Y-%m-%d"),
        "date_joined_1": fecha_registro.strftime("%H:%M:%S"),
        "last_login_0": "",
        "last_login_1": "",
    }
    if usuario.is_active:
        datos["is_active"] = "on"
    datos.update(cambios)
    return {clave: valor for clave, valor in datos.items() if valor is not None}


def aplicar_accion(cliente, accion, usuarios, **extra):
    return cliente.post(
        reverse(URL_LISTADO),
        {"action": accion, "_selected_action": [u.pk for u in usuarios], **extra},
        follow=True,
    )


# US1 — Aviso a los administradores de una solicitud nueva


def test_confirmar_registro_avisa_a_cada_administrador_activo(
    administrador,
    otro_administrador,
    confirmar_registro,
    django_capture_on_commit_callbacks,
    mailoutbox,
):
    with django_capture_on_commit_callbacks(execute=True):
        confirmar_registro()

    nuevo = get_user_model().objects.get(email="ana@lab.com")
    avisos = con_asunto(mailoutbox, ASUNTO_SOLICITUD_NUEVA)
    assert sorted(m.to[0] for m in avisos) == ["admin@lab.com", "otra.admin@lab.com"]
    enlace = url_absoluta(reverse("admin:usuarios_usuario_change", args=[nuevo.pk]))
    for aviso in avisos:
        assert len(aviso.to) == 1
        assert "Ana" in aviso.body
        assert "Pérez" in aviso.body
        assert "ana@lab.com" in aviso.body
        assert enlace in aviso.body


def test_administrador_inactivo_no_recibe_aviso(
    administrador,
    administrador_inactivo,
    confirmar_registro,
    django_capture_on_commit_callbacks,
    mailoutbox,
):
    with django_capture_on_commit_callbacks(execute=True):
        confirmar_registro()

    avisos = con_asunto(mailoutbox, ASUNTO_SOLICITUD_NUEVA)
    assert [m.to for m in avisos] == [["admin@lab.com"]]


def test_cancelar_registro_no_envia_correos(
    administrador, en_revision, django_capture_on_commit_callbacks, mailoutbox
):
    with django_capture_on_commit_callbacks(execute=True):
        en_revision.post(reverse("usuarios:registro_confirmar"), {"accion": "cancelar"})

    assert mailoutbox == []


def test_registro_sin_confirmar_no_envia_correos(
    administrador, client, datos_registro, django_capture_on_commit_callbacks, mailoutbox
):
    with django_capture_on_commit_callbacks(execute=True):
        client.post(reverse("usuarios:registro"), datos_registro)

    assert mailoutbox == []
    assert not get_user_model().objects.filter(email="ana@lab.com").exists()


def test_registro_con_correo_tomado_no_envia_correos(
    administrador, confirmar_registro, django_capture_on_commit_callbacks, mailoutbox
):
    get_user_model().objects.create_user(
        email="ana@lab.com", password=PASSWORD_EXISTENTE, first_name="Ana", last_name="Otra"
    )

    with django_capture_on_commit_callbacks(execute=True):
        confirmar_registro()

    assert mailoutbox == []
    assert get_user_model().objects.filter(email="ana@lab.com").count() == 1


def test_sin_administradores_registro_queda_pendiente(
    confirmar_registro, django_capture_on_commit_callbacks, mailoutbox, caplog
):
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        with django_capture_on_commit_callbacks(execute=True):
            confirmar_registro()

    assert not get_user_model().objects.get(email="ana@lab.com").is_active
    assert con_asunto(mailoutbox, ASUNTO_SOLICITUD_NUEVA) == []
    assert len(con_asunto(mailoutbox, ASUNTO_SOLICITUD_RECIBIDA)) == 1
    assert any(
        registro.levelno == logging.WARNING
        and "Solicitud de alta sin administradores activos para avisar" in registro.getMessage()
        for registro in caplog.records
    )


# US2 — Confirmación de solicitud recibida al solicitante


def test_confirmar_registro_envia_solicitud_recibida(
    administrador, confirmar_registro, django_capture_on_commit_callbacks, mailoutbox
):
    with django_capture_on_commit_callbacks(execute=True):
        confirmar_registro()

    recibidas = con_asunto(mailoutbox, ASUNTO_SOLICITUD_RECIBIDA)
    assert len(recibidas) == 1
    assert recibidas[0].to == ["ana@lab.com"]
    assert "Ana" in recibidas[0].body
    assert "pendiente de aprobación" in recibidas[0].body


def test_confirmacion_repetida_no_reenvia_avisos(
    administrador,
    en_revision,
    confirmar_registro,
    django_capture_on_commit_callbacks,
    mailoutbox,
):
    with django_capture_on_commit_callbacks(execute=True):
        confirmar_registro()
    cantidad = len(mailoutbox)

    with django_capture_on_commit_callbacks(execute=True):
        en_revision.post(reverse("usuarios:registro_confirmar"), {"accion": "confirmar"})

    assert cantidad == 2
    assert len(mailoutbox) == cantidad


# US3 — Aviso de aprobación al solicitante


def test_accion_aprobar_avisa_a_cada_solicitante(
    cliente_admin, usuario_pendiente, django_capture_on_commit_callbacks, mailoutbox
):
    otra = nueva_pendiente("otra@lab.com")

    with django_capture_on_commit_callbacks(execute=True):
        respuesta = aplicar_accion(cliente_admin, "aprobar_cuentas", [usuario_pendiente, otra])

    assert "Se aprobaron 2 cuenta(s)." in respuesta.content.decode()
    avisos = con_asunto(mailoutbox, ASUNTO_APROBACION)
    assert sorted(m.to for m in avisos) == [["otra@lab.com"], ["pendiente@lab.com"]]
    enlace = url_absoluta(reverse("usuarios:login"))
    assert all(enlace in aviso.body for aviso in avisos)


def test_aprobar_desde_ficha_envia_aviso(
    cliente_admin, usuario_pendiente, django_capture_on_commit_callbacks, mailoutbox
):
    with django_capture_on_commit_callbacks(execute=True):
        respuesta = cliente_admin.post(
            reverse("admin:usuarios_usuario_change", args=[usuario_pendiente.pk]),
            datos_ficha(usuario_pendiente, is_active="on"),
        )

    assert respuesta.status_code == 302
    usuario_pendiente.refresh_from_db()
    assert usuario_pendiente.is_active
    avisos = con_asunto(mailoutbox, ASUNTO_APROBACION)
    assert [m.to for m in avisos] == [["pendiente@lab.com"]]


def test_accion_aprobar_no_reenvia_a_cuentas_aprobadas(
    cliente_admin,
    usuario_pendiente,
    usuario_aprobado,
    django_capture_on_commit_callbacks,
    mailoutbox,
):
    with django_capture_on_commit_callbacks(execute=True):
        respuesta = aplicar_accion(
            cliente_admin, "aprobar_cuentas", [usuario_pendiente, usuario_aprobado]
        )

    assert "Se aprobaron 1 cuenta(s)." in respuesta.content.decode()
    assert [m.to for m in mailoutbox] == [["pendiente@lab.com"]]

    with django_capture_on_commit_callbacks(execute=True):
        aplicar_accion(cliente_admin, "aprobar_cuentas", [usuario_pendiente])

    assert len(mailoutbox) == 1


def test_guardar_ficha_de_cuenta_aprobada_no_envia_aviso(
    cliente_admin, usuario_aprobado, django_capture_on_commit_callbacks, mailoutbox
):
    with django_capture_on_commit_callbacks(execute=True):
        respuesta = cliente_admin.post(
            reverse("admin:usuarios_usuario_change", args=[usuario_aprobado.pk]),
            datos_ficha(usuario_aprobado, first_name="Pedro Pablo"),
        )

    assert respuesta.status_code == 302
    usuario_aprobado.refresh_from_db()
    assert usuario_aprobado.first_name == "Pedro Pablo"
    assert mailoutbox == []


def test_alta_desde_admin_no_envia_avisos(
    cliente_admin, django_capture_on_commit_callbacks, mailoutbox
):
    with django_capture_on_commit_callbacks(execute=True):
        respuesta = cliente_admin.post(
            reverse("admin:usuarios_usuario_add"),
            {
                "email": "nuevo@lab.com",
                "first_name": "Nuevo",
                "last_name": "Usuario",
                "usable_password": "true",
                "password1": PASSWORD_EXISTENTE,
                "password2": PASSWORD_EXISTENTE,
            },
        )

    assert respuesta.status_code == 302
    assert get_user_model().objects.filter(email="nuevo@lab.com").exists()
    assert mailoutbox == []


# US4 — Rechazo de una solicitud con aviso al solicitante


def test_rechazar_muestra_confirmacion_sin_cambios(
    cliente_admin, usuario_pendiente, django_capture_on_commit_callbacks, mailoutbox
):
    with django_capture_on_commit_callbacks(execute=True):
        respuesta = aplicar_accion(cliente_admin, "rechazar_solicitudes", [usuario_pendiente])

    contenido = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert "Rechazar solicitudes" in contenido
    assert "Pedro" in contenido
    assert "Gómez" in contenido
    assert "pendiente@lab.com" in contenido
    assert "Sí, rechazar" in contenido
    assert get_user_model().objects.filter(pk=usuario_pendiente.pk).exists()
    assert mailoutbox == []


def test_volver_desde_confirmacion_no_rechaza(cliente_admin, usuario_pendiente, mailoutbox):
    respuesta = aplicar_accion(cliente_admin, "rechazar_solicitudes", [usuario_pendiente])

    contenido = respuesta.content.decode()
    assert "No, volver" in contenido
    assert f'href="{reverse(URL_LISTADO)}"' in contenido
    usuario_pendiente.refresh_from_db()
    assert not usuario_pendiente.is_active
    assert mailoutbox == []


def test_confirmar_rechazo_elimina_y_avisa(
    cliente_admin, usuario_pendiente, django_capture_on_commit_callbacks, mailoutbox
):
    with django_capture_on_commit_callbacks(execute=True):
        respuesta = aplicar_accion(
            cliente_admin, "rechazar_solicitudes", [usuario_pendiente], confirmar="si"
        )

    assert "Se rechazaron 1 solicitud(es)." in respuesta.content.decode()
    assert not get_user_model().objects.filter(pk=usuario_pendiente.pk).exists()
    avisos = con_asunto(mailoutbox, ASUNTO_RECHAZO)
    assert [m.to for m in avisos] == [["pendiente@lab.com"]]
    assert "Pedro" in avisos[0].body
    assert len(mailoutbox) == 1


def test_cuenta_rechazada_no_puede_iniciar_sesion(client, cliente_admin, usuario_pendiente):
    aplicar_accion(cliente_admin, "rechazar_solicitudes", [usuario_pendiente], confirmar="si")

    respuesta = client.post(
        reverse("usuarios:login"),
        {"username": "pendiente@lab.com", "password": PASSWORD_EXISTENTE},
    )

    assert respuesta.status_code == 200
    assert "Usuario o contraseña incorrectos" in respuesta.content.decode()
    assert "_auth_user_id" not in client.session


def test_correo_rechazado_puede_registrarse_de_nuevo(
    client,
    cliente_admin,
    usuario_pendiente,
    datos_registro,
    django_capture_on_commit_callbacks,
    mailoutbox,
):
    aplicar_accion(cliente_admin, "rechazar_solicitudes", [usuario_pendiente], confirmar="si")

    client.post(reverse("usuarios:registro"), {**datos_registro, "email": "pendiente@lab.com"})
    with django_capture_on_commit_callbacks(execute=True):
        client.post(reverse("usuarios:registro_confirmar"), {"accion": "confirmar"})

    nueva = get_user_model().objects.get(email="pendiente@lab.com")
    assert not nueva.is_active
    assert nueva.pk != usuario_pendiente.pk
    assert len(con_asunto(mailoutbox, ASUNTO_SOLICITUD_NUEVA)) == 1
    assert len(con_asunto(mailoutbox, ASUNTO_SOLICITUD_RECIBIDA)) == 1


def test_rechazo_ignora_cuentas_aprobadas(
    cliente_admin,
    usuario_pendiente,
    usuario_aprobado,
    django_capture_on_commit_callbacks,
    mailoutbox,
):
    confirmacion = aplicar_accion(
        cliente_admin, "rechazar_solicitudes", [usuario_pendiente, usuario_aprobado]
    )
    assert "Las cuentas ya aprobadas de la selección no se van a modificar." in (
        confirmacion.content.decode()
    )

    with django_capture_on_commit_callbacks(execute=True):
        respuesta = aplicar_accion(
            cliente_admin,
            "rechazar_solicitudes",
            [usuario_pendiente, usuario_aprobado],
            confirmar="si",
        )

    assert "Se rechazaron 1 solicitud(es)." in respuesta.content.decode()
    assert not get_user_model().objects.filter(pk=usuario_pendiente.pk).exists()
    assert get_user_model().objects.get(pk=usuario_aprobado.pk).is_active
    assert [m.to for m in mailoutbox] == [["pendiente@lab.com"]]


def test_rechazar_sin_pendientes_avisa_y_no_confirma(
    cliente_admin, usuario_aprobado, django_capture_on_commit_callbacks, mailoutbox
):
    with django_capture_on_commit_callbacks(execute=True):
        respuesta = aplicar_accion(cliente_admin, "rechazar_solicitudes", [usuario_aprobado])

    contenido = respuesta.content.decode()
    assert respuesta.redirect_chain[-1][0] == reverse(URL_LISTADO)
    assert "No hay solicitudes pendientes en la selección." in contenido
    assert "Sí, rechazar" not in contenido
    assert get_user_model().objects.get(pk=usuario_aprobado.pk).is_active
    assert mailoutbox == []


# Transversales — fallas de envío y privacidad


@pytest.fixture
def envio_falla(monkeypatch):
    def falla(*args, **kwargs):
        raise SMTPException("servidor caído")

    monkeypatch.setattr("usuarios.notificaciones.send_mail", falla)


def fallas_registradas(caplog):
    return [
        registro.getMessage()
        for registro in caplog.records
        if registro.name == LOGGER and registro.levelno == logging.ERROR
    ]


def test_falla_de_envio_no_impide_registro_y_queda_en_log(
    administrador, confirmar_registro, envio_falla, django_capture_on_commit_callbacks, caplog
):
    with django_capture_on_commit_callbacks(execute=True):
        respuesta = confirmar_registro()

    assert "Registro recibido" in respuesta.content.decode()
    assert not get_user_model().objects.get(email="ana@lab.com").is_active
    fallas = fallas_registradas(caplog)
    assert "No se pudo enviar el aviso solicitud_nueva a admin@lab.com" in fallas
    assert "No se pudo enviar el aviso solicitud_recibida a ana@lab.com" in fallas


def test_falla_de_envio_no_impide_aprobacion(
    cliente_admin, usuario_pendiente, envio_falla, django_capture_on_commit_callbacks, caplog
):
    with django_capture_on_commit_callbacks(execute=True):
        respuesta = aplicar_accion(cliente_admin, "aprobar_cuentas", [usuario_pendiente])

    assert "Se aprobaron 1 cuenta(s)." in respuesta.content.decode()
    usuario_pendiente.refresh_from_db()
    assert usuario_pendiente.is_active
    assert "No se pudo enviar el aviso aprobacion a pendiente@lab.com" in fallas_registradas(caplog)


def test_correos_no_incluyen_contrasena_ni_datos_de_terceros(
    cliente_admin,
    administrador,
    confirmar_registro,
    password_registro,
    django_capture_on_commit_callbacks,
    mailoutbox,
):
    otra = nueva_pendiente("otra@lab.com")
    with django_capture_on_commit_callbacks(execute=True):
        confirmar_registro()
    ana = get_user_model().objects.get(email="ana@lab.com")
    with django_capture_on_commit_callbacks(execute=True):
        aplicar_accion(cliente_admin, "aprobar_cuentas", [ana])
    with django_capture_on_commit_callbacks(execute=True):
        aplicar_accion(cliente_admin, "rechazar_solicitudes", [otra], confirmar="si")

    asuntos = {m.subject for m in mailoutbox}
    assert asuntos == {
        ASUNTO_SOLICITUD_NUEVA,
        ASUNTO_SOLICITUD_RECIBIDA,
        ASUNTO_APROBACION,
        ASUNTO_RECHAZO,
    }
    for mensaje in mailoutbox:
        assert mensaje.subject.startswith("AquaLab")
        assert mensaje.from_email == settings.DEFAULT_FROM_EMAIL
        assert len(mensaje.to) == 1
        assert mensaje.cc == []
        assert mensaje.bcc == []
        assert password_registro not in mensaje.body
        assert PASSWORD_EXISTENTE not in mensaje.body
        assert "pbkdf2_" not in mensaje.body
    for mensaje in mailoutbox:
        if mensaje.to != ["admin@lab.com"]:
            assert "admin@lab.com" not in mensaje.body
