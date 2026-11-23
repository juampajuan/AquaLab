from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from estudios import historial


class Command(BaseCommand):
    help = (
        "Carga nueve meses de actividad de un laboratorio (clientes, muestras, estudios e "
        "informes) para el sitio publicado. Requiere AQUALAB_HISTORIAL_CONTRASENA."
    )

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("El historial requiere PostgreSQL.")
        try:
            resumen = historial.cargar_historial(self.stdout)
        except historial.HistorialError as exc:
            raise CommandError(str(exc)) from exc
        if resumen is None:
            self.stdout.write("El historial ya está cargado.")
            return
        self.stdout.write(self.style.SUCCESS("Historial cargado."))
        self.stdout.write(
            f"Clientes: {resumen.clientes} · Orígenes: {resumen.origenes} · "
            f"Muestras: {resumen.muestras} · Informes emitidos: {resumen.informes}"
        )
