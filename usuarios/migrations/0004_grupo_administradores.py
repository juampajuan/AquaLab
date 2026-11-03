from django.db import migrations

GRUPO = "Administradores"
PERMISO = "administrar_panel"


def crear_grupo(apps, schema_editor):
    alias = schema_editor.connection.alias
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    Group = apps.get_model("auth", "Group")
    # No depender de post_migrate: el permiso debe existir antes de asignarlo.
    content_type, _ = ContentType.objects.using(alias).get_or_create(
        app_label="usuarios", model="usuario"
    )
    permiso, _ = Permission.objects.using(alias).get_or_create(
        content_type=content_type,
        codename=PERMISO,
        defaults={"name": "Puede administrar el panel de AquaLab"},
    )
    grupo, _ = Group.objects.using(alias).get_or_create(name=GRUPO)
    grupo.permissions.add(permiso)


def quitar_grupo(apps, schema_editor):
    alias = schema_editor.connection.alias
    Group = apps.get_model("auth", "Group")
    grupo = Group.objects.using(alias).filter(name=GRUPO).first()
    if grupo is None:
        return
    grupo.permissions.remove(
        *grupo.permissions.filter(
            content_type__app_label="usuarios",
            content_type__model="usuario",
            codename=PERMISO,
        )
    )
    # No eliminar el permiso: puede estar asignado directamente o por otros grupos.
    if not grupo.user_set.exists() and not grupo.permissions.exists():
        grupo.delete(using=alias)


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("usuarios", "0003_estado_aprobacion"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="usuario",
            options={
                "permissions": [(PERMISO, "Puede administrar el panel de AquaLab")],
                "verbose_name": "usuario",
                "verbose_name_plural": "usuarios",
            },
        ),
        migrations.RunPython(crear_grupo, quitar_grupo),
    ]
