from django.shortcuts import render
from django.utils import timezone

from estudios.models import EstadoEstudio, Estudio
from muestras.models import Muestra


def inicio(request):
    """Panel de inicio: accesos rápidos, tres indicadores y las últimas muestras (solo lectura)."""
    contexto = {
        "muestras_sin_estudio": Muestra.objects.filter(estudios__isnull=True).count(),
        "muestras_hoy": Muestra.objects.filter(fecha_ingreso=timezone.localdate()).count(),
        "estudios_pendientes": Estudio.objects.filter(
            estado=EstadoEstudio.PENDIENTE_ANALISIS
        ).count(),
        "ultimas_muestras": Muestra.objects.select_related("cliente", "origen").order_by(
            "-numero_pi"
        )[:5],
    }
    return render(request, "inicio.html", contexto)
