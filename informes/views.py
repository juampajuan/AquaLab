from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from estudios import calculo
from estudios.forms import BuscarEstudioForm
from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Estudio
from estudios.views import RESULTADOS_POR_PAGINA

from . import servicios
from .servicios import InformeNoDisponible


def listar(request):
    page_obj = None
    q = ""
    solo_listos = request.GET.get("listos") == "1"
    form = BuscarEstudioForm(request.GET or None)
    if not form.is_bound or form.is_valid():
        q = form.cleaned_data.get("q", "") if form.is_bound else ""
        qs = servicios.estudios_para_informar(q, solo_listos)
        page_obj = Paginator(qs, RESULTADOS_POR_PAGINA).get_page(request.GET.get("page"))
    parametros = urlencode({"q": q} | ({"listos": "1"} if solo_listos else {}))
    return render(
        request,
        "informes/listar.html",
        {
            "form": form,
            "page_obj": page_obj,
            "q": q,
            "solo_listos": solo_listos,
            "parametros": parametros,
        },
    )


def control(request, pk):
    estudio = get_object_or_404(
        Estudio.objects.select_related("muestra", "muestra__cliente", "muestra__origen"), pk=pk
    )
    asignaciones = list(
        estudio.pruebas_asignadas.select_related("prueba", "medicion", "resultado").order_by(
            "prueba__codigo", "pk"
        )
    )
    todas = {a.prueba.codigo: a for a in asignaciones}
    for asignacion in asignaciones:
        # El mismo motivo que muestra estudios:detalle para una calculada sin resultado.
        asignacion.motivo_sin_resultado = calculo.motivo_sin_resultado(asignacion, todas)
    motivo = servicios.motivo_para_no_informar(estudio, asignaciones)
    return render(
        request,
        "informes/control.html",
        {
            "estudio": estudio,
            "asignaciones": asignaciones,
            "total_pruebas": len(asignaciones),
            "pruebas_completadas": sum(
                1 for a in asignaciones if a.estado == EstadoPruebaEstudio.COMPLETADA
            ),
            "motivo": motivo,
            "listo": motivo is None,
            "informe_emitido": estudio.estado == EstadoEstudio.INFORME_GENERADO,
        },
    )


@require_POST
def generar(request, pk):
    get_object_or_404(Estudio, pk=pk)
    try:
        servicios.comprobar_generacion(pk)
    except InformeNoDisponible as exc:
        messages.error(request, str(exc))
    except DatabaseError:
        messages.error(request, "No se pudo verificar el estudio. Intentá nuevamente.")
    else:
        # US 7.2: generar el informe acá, dentro de comprobar_generacion.
        messages.info(request, "La generación del informe estará disponible próximamente.")
    return redirect("informes:control", pk=pk)
