"""Política fundacional; la matriz HTTP se completa cuando existan las vistas."""

import pytest
from django.contrib.auth.models import AnonymousUser, Group
from django.core.exceptions import PermissionDenied

from usuarios.permisos_administracion import (
    autorizar_admin_django,
    autorizar_administracion,
    tiene_acceso_administracion,
)

pytestmark = pytest.mark.django_db

RUTAS_PANEL = [
    "solicitudes",
    "aprobar",
    "rechazar",
    "usuarios",
    "cambiar_rol",
    "desactivar",
    "reactivar",
    "pruebas",
]


@pytest.mark.parametrize("nombre", RUTAS_PANEL)
def test_csrf_y_metodos_autorizados(nombre, administrador_panel):
    from django.test import Client
    from django.urls import reverse

    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(administrador_panel)
    cliente.get(reverse("inicio"))
    url = ruta_panel(nombre)
    assert cliente.post(url, {}).status_code == 403
    assert cliente.put(url, HTTP_X_CSRFTOKEN=cliente.cookies["csrftoken"].value).status_code == 405


@pytest.mark.parametrize("nombre", RUTAS_PANEL)
def test_todas_las_rutas_anonimas_piden_login(nombre, client):
    assert client.get(ruta_panel(nombre)).status_code == 302


def test_revocacion_permiso_y_actor_inactivo(
    cliente_panel, administrador_panel, grupo_administradores, usuario_pendiente
):
    url = ruta_panel("aprobar", usuario_pendiente.pk)
    previa = cliente_panel.get(url)
    assert administrador_panel.has_perm("usuarios.administrar_panel")
    grupo_administradores.permissions.clear()
    assert (
        cliente_panel.post(
            url, {"accion": "confirmar", "token": previa.context["token"]}
        ).status_code
        == 403
    )
    administrador_panel.is_active = False
    administrador_panel.save(update_fields=["is_active"])
    assert cliente_panel.get(url).status_code == 302


@pytest.mark.parametrize(
    "extra", ["is_active", "aprobada", "is_superuser", "is_staff", "groups", "user_permissions"]
)
def test_campos_forjados_no_modifican(cliente_panel, usuario_pendiente, extra):
    url = ruta_panel("aprobar", usuario_pendiente.pk)
    previa = cliente_panel.get(url)
    respuesta = cliente_panel.post(
        url, {"accion": "confirmar", "token": previa.context["token"], extra: "on"}
    )
    assert respuesta.status_code == 200
    usuario_pendiente.refresh_from_db()
    assert not usuario_pendiente.aprobada and not usuario_pendiente.is_superuser


def ruta_panel(nombre, pk=999999):
    from django.urls import reverse

    return reverse(
        "administracion:" + nombre,
        args=[pk] if nombre not in {"solicitudes", "usuarios", "pruebas"} else [],
    )


@pytest.mark.parametrize("nombre", RUTAS_PANEL)
@pytest.mark.parametrize("metodo", ["get", "post"])
@pytest.mark.parametrize(
    "grupo,permiso,superusuario",
    [
        (False, False, False),
        (True, False, False),
        (False, True, False),
        (False, False, True),
        (True, False, True),
    ],
)
def test_http_sin_autorizacion_403_antes_de_objetivo(
    nombre, metodo, grupo, permiso, superusuario, django_user_model, permiso_administrativo
):
    from django.test import Client
    from django.urls import reverse

    g, _ = Group.objects.get_or_create(name="Administradores")
    g.permissions.clear()
    actor = django_user_model.objects.create_user(email="http@lab.com", is_superuser=superusuario)
    if grupo:
        actor.groups.add(g)
    if permiso:
        actor.user_permissions.add(permiso_administrativo)
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(actor)
    cliente.get(reverse("inicio"))
    csrf = cliente.cookies["csrftoken"].value
    respuesta = getattr(cliente, metodo)(ruta_panel(nombre), HTTP_X_CSRFTOKEN=csrf)
    assert respuesta.status_code == 403


def test_revocacion_entre_revision_y_confirmacion(
    cliente_panel, administrador_panel, usuario_pendiente
):
    url = ruta_panel("aprobar", usuario_pendiente.pk)
    previa = cliente_panel.get(url)
    administrador_panel.groups.clear()
    respuesta = cliente_panel.post(url, {"accion": "confirmar", "token": previa.context["token"]})
    assert respuesta.status_code == 403
    usuario_pendiente.refresh_from_db()
    assert not usuario_pendiente.aprobada


@pytest.mark.parametrize("superusuario", [False, True])
@pytest.mark.parametrize("en_grupo", [False, True])
@pytest.mark.parametrize("asignacion", ["ninguna", "directa", "otro_grupo", "administradores"])
def test_grupo_y_permiso_real(
    django_user_model, permiso_administrativo, superusuario, en_grupo, asignacion
):
    grupo, _ = Group.objects.get_or_create(name="Administradores")
    grupo.permissions.clear()
    usuario = django_user_model.objects.create_user(
        email="matriz@lab.com", is_superuser=superusuario
    )
    if en_grupo:
        usuario.groups.add(grupo)
    if asignacion == "directa":
        usuario.user_permissions.add(permiso_administrativo)
    elif asignacion == "otro_grupo":
        otro = Group.objects.create(name="Otro permiso")
        otro.permissions.add(permiso_administrativo)
        usuario.groups.add(otro)
    elif asignacion == "administradores":
        grupo.permissions.add(permiso_administrativo)
    permitido = en_grupo and asignacion != "ninguna"
    assert tiene_acceso_administracion(usuario) is permitido
    if permitido:
        autorizar_administracion(usuario)
    else:
        with pytest.raises(PermissionDenied):
            autorizar_administracion(usuario)


def test_no_staff_puede_acceder_panel(administrador_panel):
    assert not administrador_panel.is_staff
    assert tiene_acceso_administracion(administrador_panel)


@pytest.mark.parametrize("actor", [None, AnonymousUser()])
def test_sin_identidad_no_consulta(actor, django_assert_num_queries):
    with django_assert_num_queries(0):
        assert not tiene_acceso_administracion(actor)
        with pytest.raises(PermissionDenied):
            autorizar_administracion(actor)


@pytest.mark.parametrize("revocacion", ["grupo", "permiso", "activo", "eliminado"])
def test_reconsulta_actor_sin_confiar_en_cache(
    administrador_panel, grupo_administradores, django_user_model, revocacion
):
    assert administrador_panel.has_perm("usuarios.administrar_panel")
    assert tiene_acceso_administracion(administrador_panel)
    if revocacion == "grupo":
        administrador_panel.groups.remove(grupo_administradores)
    elif revocacion == "permiso":
        grupo_administradores.permissions.clear()
    elif revocacion == "activo":
        django_user_model.objects.filter(pk=administrador_panel.pk).update(is_active=False)
    else:
        django_user_model.objects.filter(pk=administrador_panel.pk).delete()
    assert not tiene_acceso_administracion(administrador_panel)
    with pytest.raises(PermissionDenied):
        autorizar_administracion(administrador_panel)


def test_permiso_otro_modelo_no_suplanta_administrativo(
    administrador_panel, grupo_administradores, django_user_model
):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    grupo_administradores.permissions.clear()
    content_type = ContentType.objects.get_for_model(Group)
    falso = Permission.objects.create(
        content_type=content_type, codename="administrar_panel", name="Otro modelo"
    )
    administrador_panel.user_permissions.add(falso)
    assert not tiene_acceso_administracion(administrador_panel)


@pytest.mark.parametrize("accion", ["change", "delete"])
def test_superusuario_sigue_autorizado_en_admin(administrador, accion):
    assert not tiene_acceso_administracion(administrador)
    autorizar_admin_django(administrador, accion)


def test_panel_no_concede_admin_y_admin_conserva_permisos(administrador_panel):
    from django.contrib.auth.models import Permission

    with pytest.raises(PermissionDenied):
        autorizar_admin_django(administrador_panel, "change")
    administrador_panel.is_staff = True
    administrador_panel.save(update_fields=["is_staff"])
    with pytest.raises(PermissionDenied):
        autorizar_admin_django(administrador_panel, "change")
    permiso = Permission.objects.get(content_type__app_label="usuarios", codename="change_usuario")
    administrador_panel.user_permissions.add(permiso)
    autorizar_admin_django(administrador_panel, "change")
    with pytest.raises(PermissionDenied):
        autorizar_admin_django(administrador_panel, "delete")


def test_politica_no_modifica_bioquimicos_ni_tipos(administrador_panel):
    from django.contrib.auth.models import Permission

    grupo, _ = Group.objects.get_or_create(name="Bioquímicos")
    permiso = Permission.objects.get(
        content_type__app_label="estudios", codename="gestionar_catalogo"
    )
    administrador_panel.groups.add(grupo)
    administrador_panel.user_permissions.add(permiso)
    grupos = set(administrador_panel.groups.values_list("pk", flat=True))
    permisos = set(administrador_panel.user_permissions.values_list("pk", flat=True))
    autorizar_administracion(administrador_panel)
    assert set(administrador_panel.groups.values_list("pk", flat=True)) == grupos
    assert set(administrador_panel.user_permissions.values_list("pk", flat=True)) == permisos
    assert administrador_panel.has_perm("estudios.gestionar_catalogo")


def test_gestor_tipos_conserva_acceso_directo_sin_panel(client, django_user_model):
    from django.contrib.auth.models import Permission
    from django.urls import reverse

    gestor = django_user_model.objects.create_user(email="gestor@lab.com")
    gestor.user_permissions.add(
        Permission.objects.get(content_type__app_label="estudios", codename="gestionar_catalogo")
    )
    assert not tiene_acceso_administracion(gestor)
    client.force_login(gestor)
    assert client.get(reverse("estudios:tipos_listar")).status_code == 200


@pytest.mark.parametrize("accion", ["change", "delete"])
def test_admin_inactivo_no_autoriza(administrador_inactivo, accion):
    with pytest.raises(PermissionDenied):
        autorizar_admin_django(administrador_inactivo, accion)
