import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def revisar_rol(cliente, usuario, rol="bioquimico"):
    url = reverse("administracion:cambiar_rol", args=[usuario.pk])
    previa = cliente.get(url)
    return cliente.post(
        url,
        {"accion": "revisar", "rol": rol, "contexto": previa.context["form"].initial["contexto"]},
    )


def test_listado_estados_roles(
    cliente_panel, usuario_pendiente, usuario_desactivado, administrador_panel, administrador
):
    respuesta = cliente_panel.get(reverse("administracion:usuarios"))
    html = respuesta.content.decode()
    for texto in [
        "Pendiente",
        "Activa",
        "Desactivada",
        "Usuario común",
        usuario_pendiente.email,
        usuario_desactivado.email,
    ]:
        assert texto in html
    assert reverse("administracion:desactivar", args=[administrador_panel.pk]) not in html
    assert reverse("administracion:cambiar_rol", args=[usuario_pendiente.pk]) not in html
    assert reverse("administracion:cambiar_rol", args=[administrador_panel.pk]) in html
    assert "Cambiar rol" in html
    assert "<select" not in html
    cuentas = {usuario.pk: usuario for usuario in respuesta.context["page_obj"]}
    assert cuentas[administrador_panel.pk].es_administrador
    assert not cuentas[administrador.pk].es_administrador
    assert html.count(">Administrador</span>") == 1


@pytest.mark.parametrize("bioquimico", [False, True])
def test_pantalla_rol_solo_ofrece_alternativas(
    cliente_panel, usuario_aprobado, grupo_bioquimicos, bioquimico
):
    if bioquimico:
        usuario_aprobado.groups.add(grupo_bioquimicos)
    url = reverse("administracion:cambiar_rol", args=[usuario_aprobado.pk])
    respuesta = cliente_panel.get(url)
    actual, nuevo = ("bioquimico", "comun") if bioquimico else ("comun", "bioquimico")
    assert [valor for valor, _ in respuesta.context["form"].fields["rol"].choices] == [nuevo]
    assert respuesta.context["form"].initial["rol"] == nuevo
    assert "Rol actual:" in respuesta.content.decode()
    invalida = cliente_panel.post(
        url,
        {
            "accion": "revisar",
            "contexto": respuesta.context["form"].initial["contexto"],
            "rol": actual,
        },
    )
    assert invalida.status_code == 200
    assert invalida.context["form"].has_error("rol")
    assert usuario_aprobado.groups.filter(pk=grupo_bioquimicos.pk).exists() == bioquimico


@pytest.mark.parametrize("caso", ["propia", "ajena", "desactivada"])
def test_rol_confirmado_y_cancelado_conserva_privilegios(
    cliente_panel,
    administrador_panel,
    usuario_aprobado,
    usuario_desactivado,
    caso,
    grupo_bioquimicos,
    otros_privilegios,
):
    usuario = {
        "propia": administrador_panel,
        "ajena": usuario_aprobado,
        "desactivada": usuario_desactivado,
    }[caso]
    activa_original = usuario.is_active
    grupo, permiso = otros_privilegios
    usuario.groups.add(grupo)
    usuario.user_permissions.add(permiso)
    profesional = grupo_bioquimicos.permissions.get(codename="validar_resultados")
    grupo.permissions.add(profesional)
    usuario.user_permissions.add(profesional)
    originales = set(usuario.groups.values_list("pk", flat=True))
    url = reverse("administracion:cambiar_rol", args=[usuario.pk])
    for accion in ["cancelar", "confirmar"]:
        previa = revisar_rol(cliente_panel, usuario)
        assert previa.status_code == 200
        cliente_panel.post(url, {"accion": accion, "token": previa.context["token"]})
        assert usuario.groups.filter(name="Bioquímicos").exists() == (accion == "confirmar")
    previa = revisar_rol(cliente_panel, usuario, "comun")
    cliente_panel.post(url, {"accion": "confirmar", "token": previa.context["token"]})
    assert set(usuario.groups.values_list("pk", flat=True)) == originales
    assert usuario.user_permissions.filter(pk=permiso.pk).exists()
    assert usuario.user_permissions.filter(pk=profesional.pk).exists()
    # Se conservan las asignaciones; el backend no habilita permisos en cuentas inactivas.
    assert (
        type(usuario).objects.get(pk=usuario.pk).has_perm("estudios.validar_resultados")
        is activa_original
    )
    usuario.refresh_from_db()
    assert usuario.is_active == activa_original


def test_error_persistencia_rol_revierte_membresia(
    cliente_panel, usuario_aprobado, grupo_bioquimicos, monkeypatch, mailoutbox
):
    from django.db import DatabaseError

    from usuarios.models import Usuario

    previa = revisar_rol(cliente_panel, usuario_aprobado)
    original = Usuario.save

    def fallar(usuario, *args, **kwargs):
        original(usuario, *args, **kwargs)
        if usuario.pk == usuario_aprobado.pk:
            raise DatabaseError("Fallo posterior a incorporar Bioquímicos")

    monkeypatch.setattr(Usuario, "save", fallar)
    respuesta = cliente_panel.post(
        reverse("administracion:cambiar_rol", args=[usuario_aprobado.pk]),
        {"accion": "confirmar", "token": previa.context["token"]},
        follow=True,
    )
    usuario_aprobado.refresh_from_db()
    assert usuario_aprobado.version_administrativa == 1
    assert not usuario_aprobado.groups.filter(pk=grupo_bioquimicos.pk).exists()
    assert "No se pudo guardar" in respuesta.content.decode()
    assert not mailoutbox


def test_usuarios_consultas_constantes_y_paginacion(cliente_panel, django_user_model):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    url = reverse("administracion:usuarios")
    with CaptureQueriesContext(connection) as pocas:
        cliente_panel.get(url)
    django_user_model.objects.bulk_create(
        [
            django_user_model(email=f"usuario{i:02}@lab.com", last_name=f"Apellido{i:02}")
            for i in range(21)
        ]
    )
    with CaptureQueriesContext(connection) as muchas:
        respuesta = cliente_panel.get(url)
    assert len(muchas) <= len(pocas) + 1
    assert len(respuesta.context["page_obj"]) == 20
    pagina = cliente_panel.get(url, {"page": 2}).context["page_obj"]
    assert len(pagina) == 2


def test_rol_invalido_y_contexto_obsoleto(cliente_panel, usuario_aprobado, otros_privilegios):
    url = reverse("administracion:cambiar_rol", args=[usuario_aprobado.pk])
    previa = cliente_panel.get(url)
    datos = {
        "accion": "revisar",
        "contexto": previa.context["form"].initial["contexto"],
        "rol": "administrador",
    }
    assert cliente_panel.post(url, datos).status_code == 200
    grupo, _ = otros_privilegios
    usuario_aprobado.groups.add(grupo)
    respuesta = cliente_panel.post(url, {**datos, "rol": "bioquimico"}, follow=True)
    assert "cambió" in respuesta.content.decode()
    assert not usuario_aprobado.groups.filter(name="Bioquímicos").exists()
