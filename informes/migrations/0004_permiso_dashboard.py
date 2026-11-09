from django.contrib.auth.management import create_permissions
from django.db import migrations

GRUPOS = ("Bioquímicos", "Administradores")
PERMISO = "ver_dashboard"


def asignar_permiso(apps, schema_editor):
    # Como en 0002: el permiso se crea acá (post_migrate llega tarde) para poder asignarlo.
    app = apps.get_app_config("informes")
    previo = getattr(app, "models_module", None)
    app.models_module = previo or True
    try:
        create_permissions(app, apps=apps, verbosity=0)
    finally:
        app.models_module = previo
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    permiso = Permission.objects.get(content_type__app_label="informes", codename=PERMISO)
    for nombre in GRUPOS:
        grupo, _ = Group.objects.get_or_create(name=nombre)
        grupo.permissions.add(permiso)


def quitar_permiso(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for grupo in Group.objects.filter(name__in=GRUPOS):
        grupo.permissions.remove(*grupo.permissions.filter(codename=PERMISO))


class Migration(migrations.Migration):
    dependencies = [
        ("informes", "0003_firmaprofesional"),
        ("estudios", "0008_grupo_bioquimicos"),
        # Sin depender de usuarios.0004: los tests de la 025 deshacen y rehacen sus migraciones, y
        # una dependencia arrastraría a esta. Administradores se obtiene o se crea igual que allá.
    ]

    operations = [
        migrations.AlterModelOptions(
            name="informe",
            options={
                "ordering": ("-numero",),
                "permissions": [
                    ("emitir_informes", "Puede emitir informes"),
                    ("ver_dashboard", "Puede ver el dashboard"),
                ],
                "verbose_name": "informe",
                "verbose_name_plural": "informes",
            },
        ),
        migrations.RunPython(asignar_permiso, quitar_permiso),
    ]
