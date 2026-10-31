from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from pruebas.importacion import ErrorImportacion, importar

DATOS = settings.BASE_DIR / "pruebas" / "datos"


class Command(BaseCommand):
    help = "Importa el catálogo de pruebas de agua y sus límites por tipo de vertido."

    def add_arguments(self, parser):
        parser.add_argument("--catalogo", type=Path, default=DATOS / "catalogo_pruebas_agua.csv")
        parser.add_argument("--limites", type=Path, default=DATOS / "limites_vertido.csv")

    def handle(self, *args, catalogo, limites, **options):
        try:
            resumen = importar(Path(catalogo), Path(limites))
        except ErrorImportacion as error:
            cantidad = len(error.errores)
            errores = "1 error" if cantidad == 1 else f"{cantidad} errores"
            raise CommandError(
                f"No se importó nada: el archivo tiene {errores}.\n" + "\n".join(error.errores)
            ) from error
        pruebas = resumen.pruebas_creadas + resumen.pruebas_actualizadas
        limites_total = resumen.limites_creados + resumen.limites_actualizados
        self.stdout.write(
            self.style.SUCCESS(
                f"Catálogo importado: {pruebas} pruebas ({resumen.pruebas_creadas} creadas, "
                f"{resumen.pruebas_actualizadas} actualizadas) y {limites_total} límites por "
                f"tipo de vertido ({resumen.limites_creados} creados, "
                f"{resumen.limites_actualizados} actualizados)."
            )
        )
        for aviso in resumen.avisos:
            self.stdout.write(self.style.WARNING(aviso))
