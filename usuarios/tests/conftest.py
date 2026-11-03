import pytest
from django.test import Client
from django.urls import reverse

PASSWORD_REGISTRO = "Clave-Secreta-Unica-987"
PASSWORD_EXISTENTE = "Clave-Existente-Segura-654"


@pytest.fixture
def password_registro():
    return PASSWORD_REGISTRO


@pytest.fixture
def datos_registro(password_registro):
    return {
        "first_name": "Ana",
        "last_name": "Pérez",
        "email": "ana@lab.com",
        "password1": password_registro,
        "password2": password_registro,
    }


@pytest.fixture
def usuario_pendiente(django_user_model):
    return django_user_model.objects.create_user(
        email="pendiente@lab.com",
        password=PASSWORD_EXISTENTE,
        first_name="Pedro",
        last_name="Gómez",
        is_active=False,
    )


@pytest.fixture
def usuario_aprobado(django_user_model):
    return django_user_model.objects.create_user(
        email="aprobado@lab.com",
        password=PASSWORD_EXISTENTE,
        first_name="Pedro",
        last_name="Gómez",
        is_active=True,
    )


@pytest.fixture
def administrador(django_user_model):
    return django_user_model.objects.create_superuser(
        email="admin@lab.com",
        password=PASSWORD_EXISTENTE,
        first_name="Admin",
        last_name="AquaLab",
    )


@pytest.fixture
def otro_administrador(django_user_model):
    return django_user_model.objects.create_superuser(
        email="otra.admin@lab.com",
        password=PASSWORD_EXISTENTE,
        first_name="Otra",
        last_name="Admin",
    )


@pytest.fixture
def administrador_inactivo(django_user_model):
    administrador = django_user_model.objects.create_superuser(
        email="admin.inactivo@lab.com",
        password=PASSWORD_EXISTENTE,
        first_name="Admin",
        last_name="Inactivo",
    )
    administrador.is_active = False
    administrador.save(update_fields=["is_active"])
    return administrador


@pytest.fixture
def confirmar_registro(en_revision):
    """Confirma el registro que dejó `en_revision` y devuelve la respuesta final."""

    def confirmar():
        return en_revision.post(
            reverse("usuarios:registro_confirmar"), {"accion": "confirmar"}, follow=True
        )

    return confirmar


@pytest.fixture
def cliente_admin(administrador):
    cliente = Client()
    cliente.force_login(administrador)
    return cliente


@pytest.fixture
def en_revision(client, datos_registro):
    """Deja el registro en revisión: los datos quedan en `session["registro_pendiente"]`."""
    client.post(reverse("usuarios:registro"), datos_registro)
    return client


@pytest.fixture
def cliente_csrf():
    return Client(enforce_csrf_checks=True)


@pytest.fixture
def permiso_administrativo(db):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    from usuarios.models import Usuario

    return Permission.objects.get_or_create(
        content_type=ContentType.objects.get_for_model(Usuario),
        codename="administrar_panel",
        defaults={"name": "Puede administrar el panel de AquaLab"},
    )[0]


@pytest.fixture
def grupo_administradores(permiso_administrativo):
    from django.contrib.auth.models import Group

    grupo, _ = Group.objects.get_or_create(name="Administradores")
    grupo.permissions.add(permiso_administrativo)
    return grupo


@pytest.fixture
def administrador_panel(django_user_model, grupo_administradores):
    usuario = django_user_model.objects.create_user(
        email="panel@lab.com", password=PASSWORD_EXISTENTE, first_name="Panel", last_name="Admin"
    )
    usuario.groups.add(grupo_administradores)
    return usuario


@pytest.fixture
def usuario_desactivado(django_user_model):
    return django_user_model.objects.create_user(
        email="desactivado@lab.com",
        password=PASSWORD_EXISTENTE,
        first_name="Cuenta",
        last_name="Desactivada",
        aprobada=True,
        is_active=False,
    )


@pytest.fixture
def grupo_bioquimicos(db):
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType

    from estudios.models import Validacion
    from informes.models import Informe

    grupo, _ = Group.objects.get_or_create(name="Bioquímicos")
    for modelo, codigo in [(Validacion, "validar_resultados"), (Informe, "emitir_informes")]:
        permiso, _ = Permission.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(modelo),
            codename=codigo,
            defaults={"name": codigo},
        )
        grupo.permissions.add(permiso)
    return grupo


@pytest.fixture
def historial_usuario(db):
    def crear(usuario, relacion):
        from datetime import date

        from clientes.models import Cliente
        from informes.models import FirmaProfesional
        from muestras.models import Muestra, Origen

        if relacion == "firma":
            return FirmaProfesional.objects.create(
                usuario=usuario, imagen=b"firma", matricula="MP 1"
            )
        cliente = Cliente.objects.create(
            nombre="Histórico",
            tipo_documento="DNI",
            numero_documento="12345678",
            email="cliente@lab.com",
        )
        origen = Origen.objects.create(cliente=cliente, nombre="Pozo")
        return Muestra.objects.create(
            numero_pi=200001,
            nombre="Agua",
            cliente=cliente,
            origen=origen,
            fecha_muestreo=date(2026, 1, 1),
            fecha_ingreso=date(2026, 1, 1),
            sitio_extraccion="Pozo",
            registrada_por=usuario,
        )

    return crear


@pytest.fixture
def otros_privilegios(db, permiso_administrativo):
    from django.contrib.auth.models import Group

    grupo, _ = Group.objects.get_or_create(name="Otros privilegios")
    grupo.permissions.add(permiso_administrativo)
    return grupo, permiso_administrativo


@pytest.fixture
def cliente_panel(client, administrador_panel):
    client.force_login(administrador_panel)
    return client
