from django.contrib.auth.management import create_permissions
from django.db import migrations

GRUPO = "Bioquímicos"
PERMISO = "emitir_informes"


def asignar_permiso(apps, schema_editor):
    # Los permisos se crean recién en post_migrate: se crean acá para poder asignarlos. La app
    # histórica no tiene models_module y create_permissions la saltearía (igual que estudios.0008).
    app = apps.get_app_config("informes")
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
        Permission.objects.get(content_type__app_label="informes", codename=PERMISO)
    )


def quitar_permiso(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    grupo = Group.objects.filter(name=GRUPO).first()
    if grupo is not None:
        grupo.permissions.remove(*grupo.permissions.filter(codename=PERMISO))


class Migration(migrations.Migration):
    dependencies = [
        ("informes", "0001_initial"),
        ("estudios", "0008_grupo_bioquimicos"),
    ]

    operations = [migrations.RunPython(asignar_permiso, quitar_permiso)]
