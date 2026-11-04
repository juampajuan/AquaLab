"""Migraciones reales sobre la base de test PostgreSQL, restaurando siempre el esquema."""

import importlib
from datetime import date

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

ANTERIOR = ("usuarios", "0002_alter_usuario_date_joined_alter_usuario_is_active")
ESTADOS = ("usuarios", "0003_estado_aprobacion")
GRUPO = ("usuarios", "0004_grupo_administradores")

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def migraciones_usuarios():
    executor = MigrationExecutor(connection)
    finales = executor.loader.graph.leaf_nodes()
    otras = [nodo for nodo in finales if nodo[0] != "usuarios"]

    def migrar(nodo):
        executor = MigrationExecutor(connection)
        objetivos = [*otras, nodo]
        executor.migrate(objetivos)
        return executor.loader.project_state(objetivos).apps

    try:
        yield migrar
    finally:
        MigrationExecutor(connection).migrate(finales)


def test_backfill_conserva_identidades_permisos_y_referencias(migraciones_usuarios):
    antiguas = migraciones_usuarios(ANTERIOR)
    Usuario = antiguas.get_model("usuarios", "Usuario")
    Group = antiguas.get_model("auth", "Group")
    Permission = antiguas.get_model("auth", "Permission")
    grupo = Group.objects.create(name="Grupo histórico")
    permiso = Permission.objects.get(content_type__app_label="usuarios", codename="change_usuario")
    usuarios = [
        Usuario.objects.create(
            email="activa@historia.com",
            first_name="Activa",
            last_name="Histórica",
            password="hash-A",
        ),
        Usuario.objects.create(email="inactiva@historia.com", is_active=False, password="hash-B"),
        Usuario.objects.create(
            email="super@historia.com",
            is_active=False,
            is_staff=True,
            is_superuser=True,
            password="hash-C",
        ),
    ]
    inactiva = usuarios[1]
    inactiva.groups.add(grupo)
    inactiva.user_permissions.add(permiso)
    # Un last_login y una firma no se interpretan como evidencia automática de aprobación.
    inactiva.last_login = inactiva.date_joined
    inactiva.save(update_fields=["last_login"])
    Firma = antiguas.get_model("informes", "FirmaProfesional")
    firma = Firma.objects.create(
        usuario_id=inactiva.pk, imagen=b"firma-historica", matricula="MP 1"
    )
    Cliente = antiguas.get_model("clientes", "Cliente")
    Origen = antiguas.get_model("muestras", "Origen")
    Muestra = antiguas.get_model("muestras", "Muestra")
    cliente = Cliente.objects.create(
        nombre="Histórico", tipo_documento="DNI", numero_documento="12345678", email="c@lab.com"
    )
    origen = Origen.objects.create(cliente_id=cliente.pk, nombre="Pozo")
    muestra = Muestra.objects.create(
        numero_pi=200001,
        nombre="Agua",
        cliente_id=cliente.pk,
        origen_id=origen.pk,
        fecha_muestreo=date(2026, 1, 1),
        fecha_ingreso=date(2026, 1, 1),
        sitio_extraccion="Pozo",
        registrada_por_id=inactiva.pk,
    )
    originales = {u.pk: Usuario.objects.values().get(pk=u.pk) for u in usuarios}

    actuales = migraciones_usuarios(GRUPO)
    UsuarioNuevo = actuales.get_model("usuarios", "Usuario")
    for pk, original in originales.items():
        actual = UsuarioNuevo.objects.values().get(pk=pk)
        assert actual.pop("aprobada") is original["is_active"]
        assert actual.pop("version_administrativa") == 1
        assert actual == original
    conservada = UsuarioNuevo.objects.get(pk=inactiva.pk)
    assert list(conservada.groups.values_list("pk", flat=True)) == [grupo.pk]
    assert list(conservada.user_permissions.values_list("pk", flat=True)) == [permiso.pk]
    muestra_conservada = actuales.get_model("muestras", "Muestra").objects.get(pk=muestra.pk)
    firma_conservada = actuales.get_model("informes", "FirmaProfesional").objects.get(pk=firma.pk)
    assert muestra_conservada.registrada_por_id == inactiva.pk
    assert bytes(firma_conservada.imagen) == b"firma-historica"
    administradores = actuales.get_model("auth", "Group").objects.get(name="Administradores")
    assert not administradores.user_set.exists()


def test_default_temporal_no_aprueba_inactivos_y_default_final_es_compatible(migraciones_usuarios):
    antiguas = migraciones_usuarios(ANTERIOR)
    Usuario = antiguas.get_model("usuarios", "Usuario")
    pendiente = Usuario.objects.create(email="pendiente@historia.com", is_active=False)
    actuales = migraciones_usuarios(ESTADOS)
    Nuevo = actuales.get_model("usuarios", "Usuario")
    assert not Nuevo.objects.get(pk=pendiente.pk).aprobada
    directa = Nuevo.objects.create(email="directa@historia.com")
    assert directa.aprobada and directa.is_active


def test_grupo_idempotente_conserva_miembros_y_otros_permisos(migraciones_usuarios):
    apps = migraciones_usuarios(ESTADOS)
    Usuario = apps.get_model("usuarios", "Usuario")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    grupo, _ = Group.objects.get_or_create(name="Administradores")
    adicional = Permission.objects.get(
        content_type__app_label="usuarios", codename="change_usuario"
    )
    grupo.permissions.add(adicional)
    miembro = Usuario.objects.create(email="miembro@historia.com")
    miembro.groups.add(grupo)
    bioquimicos, _ = Group.objects.get_or_create(name="Bioquímicos")
    bioquimicos.permissions.add(adicional)
    miembro.groups.add(bioquimicos)
    bio_antes = set(bioquimicos.permissions.values_list("pk", flat=True))

    apps = migraciones_usuarios(GRUPO)
    migracion = importlib.import_module("usuarios.migrations.0004_grupo_administradores")
    with connection.schema_editor() as schema_editor:
        migracion.crear_grupo(apps, schema_editor)
        migracion.crear_grupo(apps, schema_editor)
    grupo = apps.get_model("auth", "Group").objects.get(pk=grupo.pk)
    assert grupo.user_set.filter(pk=miembro.pk).exists()
    assert grupo.permissions.filter(pk=adicional.pk).exists()
    assert (
        grupo.permissions.filter(
            content_type__app_label="usuarios",
            content_type__model="usuario",
            codename="administrar_panel",
        ).count()
        == 1
    )
    bio_despues = apps.get_model("auth", "Group").objects.get(pk=bioquimicos.pk)
    assert set(bio_despues.permissions.values_list("pk", flat=True)) == bio_antes

    # La reversión solo retira la asignación propia, no miembros ni otros permisos.
    apps = migraciones_usuarios(ESTADOS)
    grupo = apps.get_model("auth", "Group").objects.get(pk=grupo.pk)
    assert grupo.user_set.filter(pk=miembro.pk).exists()
    assert grupo.permissions.filter(pk=adicional.pk).exists()
    assert not grupo.permissions.filter(codename="administrar_panel").exists()
    assert apps.get_model("usuarios", "Usuario").objects.get(pk=miembro.pk).is_active


def test_reversion_conserva_estado_anterior_sin_activar(migraciones_usuarios):
    apps = migraciones_usuarios(ANTERIOR)
    Usuario = apps.get_model("usuarios", "Usuario")
    inactiva = Usuario.objects.create(
        email="inactiva@historia.com", is_active=False, password="hash"
    )
    original = Usuario.objects.values().get(pk=inactiva.pk)
    migraciones_usuarios(GRUPO)
    anteriores = migraciones_usuarios(ANTERIOR)
    assert (
        anteriores.get_model("usuarios", "Usuario").objects.values().get(pk=inactiva.pk) == original
    )


def test_reversion_no_quita_asignaciones_administrativas_ajenas(migraciones_usuarios):
    apps = migraciones_usuarios(GRUPO)
    Usuario = apps.get_model("usuarios", "Usuario")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    permiso = Permission.objects.get(
        content_type__app_label="usuarios", codename="administrar_panel"
    )
    usuario = Usuario.objects.create(email="asignacion@historia.com")
    usuario.user_permissions.add(permiso)
    otro = Group.objects.create(name="Permiso administrativo por otra vía")
    otro.permissions.add(permiso)
    usuario.groups.add(otro)

    apps = migraciones_usuarios(ESTADOS)
    conservado = apps.get_model("usuarios", "Usuario").objects.get(pk=usuario.pk)
    assert conservado.user_permissions.filter(pk=permiso.pk).exists()
    assert conservado.groups.get(pk=otro.pk).permissions.filter(pk=permiso.pk).exists()
