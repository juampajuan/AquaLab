import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from estudios import demo

MENSAJE_ENTORNO = (
    "cargar_demo solo corre en desarrollo: requiere AQUALAB_ENTORNO=desarrollo y DEBUG=True."
)


class Command(BaseCommand):
    help = (
        "Carga datos de demo (SCRUM-78): seis meses de muestras, estudios e informes ficticios. "
        "Solo en desarrollo."
    )

    def handle(self, *args, **options):
        entorno = os.environ.get("AQUALAB_ENTORNO", "").strip().lower()
        if entorno != "desarrollo" or not settings.DEBUG:
            raise CommandError(MENSAJE_ENTORNO)
        if connection.vendor != "postgresql":
            raise CommandError("La demo requiere PostgreSQL.")
        try:
            resumen = demo.cargar_demo(self.stdout)
        except demo.DemoError as exc:
            raise CommandError(str(exc)) from exc
        except Exception as exc:
            raise CommandError(f"No se pudo cargar la demo: {exc}. No se guardó nada.") from exc
        if resumen is None:
            self.stdout.write(demo.MENSAJE_YA_CARGADA)
            return
        if resumen.catalogo_importado:
            self.stdout.write("Se importó el catálogo de pruebas porque estaba vacío.")
        self.stdout.write(self.style.SUCCESS("Demo cargada."))
        self.stdout.write(
            f"Clientes: {resumen.clientes} · Orígenes: {resumen.origenes} · "
            f"Muestras: {resumen.muestras} · Informes emitidos: {resumen.informes}"
        )
        self.stdout.write("Estudios por estado:")
        for etiqueta, cantidad in resumen.estudios.items():
            self.stdout.write(f"  {etiqueta}: {cantidad}")
        self.stdout.write(f"Usuarios (contraseña {demo.CONTRASENA}):")
        for datos in demo.USUARIOS:
            self.stdout.write(f"  {datos['email']}")
