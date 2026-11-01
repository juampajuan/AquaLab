from django.contrib.auth.management import create_permissions
from django.db import migrations

GRUPO = "Bioquímicos"
PERMISO = "validar_resultados"


def crear_grupo(apps, schema_editor):
    # Los permisos se crean recién en post_migrate: se crean acá para poder asignarlos. La app
    # histórica no tiene models_module y create_permissions la saltearía.
    app = apps.get_app_config("estudios")
    previo = getattr(app, "models_module", None)
    app.models_module = previo or True
    try:
        create_permissions(app, apps=apps, verbosity=0)
    finally:
        app.models_module = previo
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    grupo, _ = Group.objects.get_or_create(name=GRUPO)
    grupo.permissions.add(
        Permission.objects.get(content_type__app_label="estudios", codename=PERMISO)
    )


def quitar_grupo(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    grupo = Group.objects.filter(name=GRUPO).first()
    if grupo is None:
        return
    grupo.permissions.remove(*grupo.permissions.filter(codename=PERMISO))
    if not grupo.permissions.exists() and not grupo.user_set.exists():
        grupo.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("estudios", "0007_validacion"),
    ]

    operations = [migrations.RunPython(crear_grupo, quitar_grupo)]
