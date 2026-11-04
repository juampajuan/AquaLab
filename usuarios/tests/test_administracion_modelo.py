"""Fundamentos: aprobación previa separada de habilitación (FR-010)."""

import pytest
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse

from .conftest import PASSWORD_EXISTENTE

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("campos", "estado", "aprobada", "activa"),
    [
        ({}, "activa", True, True),
        ({"is_active": False}, "pendiente", False, False),
        ({"is_active": False, "aprobada": True}, "desactivada", True, False),
    ],
)
def test_estados_derivados_y_manager(django_user_model, campos, estado, aprobada, activa):
    usuario = django_user_model.objects.create_user(
        email="  Estado@LAB.com ", password=PASSWORD_EXISTENTE, **campos
    )
    usuario.refresh_from_db()
    assert usuario.estado_cuenta == estado
    assert usuario.aprobada is aprobada
    assert usuario.is_active is activa
    assert usuario.version_administrativa == 1
    assert usuario.email == "estado@lab.com"
    assert usuario.check_password(PASSWORD_EXISTENTE)


@pytest.mark.parametrize(
    ("aprobada", "activa", "estado"),
    [(False, False, "Pendiente"), (True, True, "Activa"), (True, False, "Desactivada")],
)
def test_etiquetas_de_estado(django_user_model, aprobada, activa, estado):
    usuario = django_user_model(aprobada=aprobada, is_active=activa)
    assert usuario.estado_cuenta.label == estado


def test_defaults_y_campos_internos(django_user_model):
    usuario = django_user_model.objects.create(email="directa@lab.com")
    assert usuario.aprobada and usuario.is_active
    assert usuario.version_administrativa == 1
    assert not django_user_model._meta.get_field("aprobada").editable
    assert not django_user_model._meta.get_field("version_administrativa").editable
    assert django_user_model._meta.get_field("is_active").verbose_name == "activa"


def test_manager_rechaza_activa_sin_aprobar(django_user_model):
    with pytest.raises(ValueError, match="activa.*aprobada"):
        django_user_model.objects.create_user(email="invalida@lab.com", aprobada=False)
    assert not django_user_model.objects.filter(email="invalida@lab.com").exists()


def test_constraint_is_active_implica_aprobada(django_user_model, usuario_pendiente):
    # «is_active=False OR aprobada=True»: tampoco update puede eludir la regla.
    with pytest.raises(IntegrityError), transaction.atomic():
        django_user_model.objects.filter(pk=usuario_pendiente.pk).update(is_active=True)
    with pytest.raises(IntegrityError), transaction.atomic():
        django_user_model.objects.create(email="invalida@lab.com", aprobada=False, is_active=True)
    usuario_pendiente.refresh_from_db()
    assert not usuario_pendiente.aprobada and not usuario_pendiente.is_active


def test_full_clean_valida_invariante(django_user_model):
    usuario = django_user_model(
        email="invalida@lab.com", first_name="Ana", last_name="Pérez", aprobada=False
    )
    usuario.set_password(PASSWORD_EXISTENTE)
    with pytest.raises(ValidationError, match="aprobada"):
        usuario.full_clean()


@pytest.mark.parametrize("version", [0, -1])
def test_version_administrativa_positiva(django_user_model, version):
    # «versión >=1» se aplica incluso ante escrituras directas.
    with pytest.raises(IntegrityError), transaction.atomic():
        django_user_model.objects.create(email="version@lab.com", version_administrativa=version)


def test_superusuario_aprobado_no_recibe_grupo(django_user_model):
    usuario = django_user_model.objects.create_superuser(
        email="super@lab.com", password=PASSWORD_EXISTENTE, aprobada=False, is_active=False
    )
    assert usuario.aprobada and usuario.is_active and usuario.is_staff and usuario.is_superuser
    assert not usuario.groups.filter(name="Administradores").exists()


def test_registro_publico_sigue_creando_pendiente(client, datos_registro, django_user_model):
    client.post(reverse("usuarios:registro"), datos_registro)
    respuesta = client.post(reverse("usuarios:registro_confirmar"), {"accion": "confirmar"})
    assert respuesta.status_code == 302
    usuario = django_user_model.objects.get(email=datos_registro["email"].lower())
    assert usuario.estado_cuenta == "pendiente"
    assert not usuario.aprobada and not usuario.is_active
    assert usuario.version_administrativa == 1


def test_suspension_conserva_aprobacion_y_no_autentica(usuario_desactivado):
    assert usuario_desactivado.aprobada
    assert usuario_desactivado.estado_cuenta == "desactivada"
    assert authenticate(email=usuario_desactivado.email, password=PASSWORD_EXISTENTE) is None


def test_panel_solo_modifica_pertenencia_bioquimicos(
    administrador_panel, grupo_bioquimicos, otros_privilegios
):
    from usuarios.servicios_administracion import cambiar_rol_panel

    from .test_administracion_servicios import peticion

    grupo, permiso = otros_privilegios
    administrador_panel.groups.add(grupo)
    administrador_panel.user_permissions.add(permiso)
    grupos = set(administrador_panel.groups.values_list("pk", flat=True))
    permisos = set(administrador_panel.user_permissions.values_list("pk", flat=True))
    for bioquimico, version in [(True, 1), (False, 2)]:
        cambiar_rol_panel(
            peticion(administrador_panel), administrador_panel.pk, bioquimico, version
        )
        administrador_panel.refresh_from_db()
        assert administrador_panel.aprobada and administrador_panel.is_active
        esperados = grupos | {grupo_bioquimicos.pk} if bioquimico else grupos
        assert set(administrador_panel.groups.values_list("pk", flat=True)) == esperados
        assert set(administrador_panel.user_permissions.values_list("pk", flat=True)) == permisos
