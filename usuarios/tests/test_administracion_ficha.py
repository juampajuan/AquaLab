"""El admin conserva su política y rechaza propuestas antiguas antes de guardar M2M."""

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from usuarios.servicios_administracion import cambiar_estado_panel

from .test_administracion_servicios import peticion
from .test_notificaciones import aplicar_accion, datos_ficha

pytestmark = pytest.mark.django_db


def test_ficha_obsoleta_no_pierde_grupos(cliente_admin, usuario_aprobado, administrador_panel):
    datos = datos_ficha(cliente_admin, usuario_aprobado, first_name="Obsoleto")
    cambiar_estado_panel(peticion(administrador_panel), usuario_aprobado.pk, False, 1)
    grupo = Group.objects.create(name="Otra pertenencia")
    usuario_aprobado.groups.add(grupo)
    respuesta = cliente_admin.post(
        reverse("admin:usuarios_usuario_change", args=[usuario_aprobado.pk]), datos
    )
    assert respuesta.status_code == 200
    assert respuesta.context["adminform"].form.non_field_errors()
    usuario_aprobado.refresh_from_db()
    assert not usuario_aprobado.is_active
    assert usuario_aprobado.first_name != "Obsoleto"
    assert usuario_aprobado.groups.filter(pk=grupo.pk).exists()


def test_ficha_m2m_incrementa_revision(
    cliente_admin, usuario_aprobado, grupo_administradores, permiso_administrativo
):
    datos = datos_ficha(
        cliente_admin,
        usuario_aprobado,
        groups=[grupo_administradores.pk],
        user_permissions=[permiso_administrativo.pk],
    )
    respuesta = cliente_admin.post(
        reverse("admin:usuarios_usuario_change", args=[usuario_aprobado.pk]), datos
    )
    assert respuesta.status_code == 302
    usuario_aprobado.refresh_from_db()
    assert usuario_aprobado.version_administrativa == 2
    assert usuario_aprobado.groups.filter(pk=grupo_administradores.pk).exists()
    assert usuario_aprobado.user_permissions.filter(pk=permiso_administrativo.pk).exists()


def test_ficha_no_desactiva_propio_admin(cliente_admin, administrador):
    datos = datos_ficha(
        cliente_admin, administrador, is_active=None, is_staff="on", is_superuser="on"
    )
    respuesta = cliente_admin.post(
        reverse("admin:usuarios_usuario_change", args=[administrador.pk]), datos
    )
    assert respuesta.status_code == 200
    administrador.refresh_from_db()
    assert administrador.is_active
    assert "No podés desactivar tu propia cuenta" in respuesta.content.decode()


@pytest.mark.parametrize("relacion", ["firma", "muestra"])
def test_admin_informa_rechazo_impedido(
    cliente_admin,
    usuario_pendiente,
    historial_usuario,
    relacion,
    django_capture_on_commit_callbacks,
    mailoutbox,
):
    referencia = historial_usuario(usuario_pendiente, relacion)
    with django_capture_on_commit_callbacks(execute=True):
        respuesta = aplicar_accion(
            cliente_admin, "rechazar_solicitudes", [usuario_pendiente], confirmar="si"
        )
    assert "No se puede rechazar" in respuesta.content.decode()
    usuario_pendiente.refresh_from_db()
    referencia.refresh_from_db()
    assert not mailoutbox


def test_ficha_sin_firma_no_guarda(cliente_admin, usuario_aprobado):
    datos = datos_ficha(cliente_admin, usuario_aprobado, first_name="Forjado")
    datos.pop("contexto_administrativo")
    respuesta = cliente_admin.post(
        reverse("admin:usuarios_usuario_change", args=[usuario_aprobado.pk]), datos
    )
    assert respuesta.status_code == 200
    usuario_aprobado.refresh_from_db()
    assert usuario_aprobado.first_name != "Forjado"


def test_ficha_ajena_a_sesion_no_guarda(cliente_admin, administrador, usuario_aprobado):
    from django.test import Client

    datos = datos_ficha(cliente_admin, usuario_aprobado, first_name="Ajeno")
    otro = Client()
    otro.force_login(administrador)
    respuesta = otro.post(
        reverse("admin:usuarios_usuario_change", args=[usuario_aprobado.pk]), datos
    )
    assert respuesta.status_code == 200
    usuario_aprobado.refresh_from_db()
    assert usuario_aprobado.first_name != "Ajeno"


def test_cambio_clave_invalida_ficha_abierta(cliente_admin, usuario_aprobado):
    datos = datos_ficha(cliente_admin, usuario_aprobado, first_name="Anterior")
    respuesta = cliente_admin.post(
        reverse("admin:auth_user_password_change", args=[usuario_aprobado.pk]),
        {"password1": "NuevaClaveSuperSegura2026!", "password2": "NuevaClaveSuperSegura2026!"},
    )
    assert respuesta.status_code == 302
    respuesta = cliente_admin.post(
        reverse("admin:usuarios_usuario_change", args=[usuario_aprobado.pk]), datos
    )
    assert respuesta.status_code == 200
    usuario_aprobado.refresh_from_db()
    assert usuario_aprobado.check_password("NuevaClaveSuperSegura2026!")
    assert usuario_aprobado.first_name != "Anterior"
