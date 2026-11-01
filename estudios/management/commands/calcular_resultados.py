from django.core.management.base import BaseCommand
from django.db import transaction

from estudios import calculo
from estudios.models import Estudio, PruebaEstudio, Resultado


class Command(BaseCommand):
    help = (
        "Calcula los resultados de las mediciones que todavía no tienen (cargadas antes de US 6.2)."
    )

    def handle(self, *args, **options):
        antes = Resultado.objects.count()
        sin_calcular = 0
        pendientes = PruebaEstudio.objects.filter(medicion__isnull=False, resultado__isnull=True)
        for estudio_pk in pendientes.values_list("estudio", flat=True).distinct():
            with transaction.atomic():
                estudio = Estudio.objects.select_for_update().get(pk=estudio_pk)
                asignaciones = pendientes.filter(estudio=estudio).select_related("prueba")
                sin_calcular += len(calculo.recalcular(estudio, list(asignaciones)))
        calculados = Resultado.objects.count() - antes
        self.stdout.write(f"Resultados calculados: {calculados}. Sin calcular: {sin_calcular}.")
