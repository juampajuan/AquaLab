import logging
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from estudios import calculo
from estudios.forms import BuscarEstudioForm
from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Estudio
from estudios.views import RESULTADOS_POR_PAGINA

from . import pdf, servicios
from .busqueda import informes_emitidos
from .contenido import armar_contenido
from .forms import BuscarInformeForm, FirmaForm
from .models import FirmaProfesional, Informe
from .servicios import EmitirInformeError, InformeNoDisponible

logger = logging.getLogger("informes")


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
            "informe": Informe.objects.filter(estudio=estudio).first(),
        },
    )


def vista_previa(request, pk):
    """Borrador del informe (US 7.2): cualquier empleado lo ve; no cambia nada."""
    estudio = get_object_or_404(
        Estudio.objects.select_related("muestra", "muestra__cliente", "muestra__origen"), pk=pk
    )
    motivo = servicios.motivo_para_no_informar(estudio, list(estudio.pruebas_asignadas.all()))
    if motivo:
        messages.error(request, motivo)
        return redirect("informes:control", pk=estudio.pk)
    puede_emitir = request.user.has_perm("informes.emitir_informes")
    contexto = {
        "estudio": estudio,
        "contenido": armar_contenido(estudio, request.user),
        "puede_emitir": puede_emitir,
        "falta_firma": puede_emitir
        and not FirmaProfesional.objects.filter(usuario=request.user).exists(),
    }
    return render(request, "informes/vista_previa.html", contexto)


@permission_required("informes.emitir_informes", raise_exception=True)
@require_POST
def generar(request, pk):
    """Emite el informe (US 7.2), confirmado desde la vista previa."""
    get_object_or_404(Estudio, pk=pk)
    try:
        informe = servicios.emitir_informe(pk, request.user)
    except (InformeNoDisponible, EmitirInformeError) as exc:
        messages.error(request, str(exc))
    except DatabaseError:
        messages.error(request, "No se pudo emitir el informe. Intentá nuevamente.")
    else:
        messages.success(
            request, f"Se emitió el informe {informe.numero_mostrado} del estudio {pk}."
        )
        return redirect("informes:ver", pk=pk)
    return redirect("informes:control", pk=pk)


def ver(request, pk):
    """El informe emitido, siempre desde su copia (FR-010)."""
    informe = get_object_or_404(
        Informe.objects.select_related("estudio", "emitido_por"), estudio__pk=pk
    )
    contexto = {"estudio": informe.estudio, "informe": informe, "contenido": informe.contenido}
    return render(request, "informes/ver.html", contexto)


def emitidos(request):
    """Listado y búsqueda de informes emitidos (US 7.3): cualquier empleado con sesión."""
    page_obj = None
    form = BuscarInformeForm(request.GET or None)
    datos = {"q": "", "desde": None, "hasta": None}
    if form.is_bound and form.is_valid():
        datos = form.cleaned_data
    if not form.is_bound or form.is_valid():
        qs = informes_emitidos(datos["q"], datos["desde"], datos["hasta"])
        page_obj = Paginator(qs, RESULTADOS_POR_PAGINA).get_page(request.GET.get("page"))
    parametros = urlencode(
        {
            clave: valor.isoformat() if hasattr(valor, "isoformat") else valor
            for clave, valor in datos.items()
            if valor
        }
    )
    return render(
        request,
        "informes/emitidos.html",
        {
            "form": form,
            "page_obj": page_obj,
            "parametros": parametros,
            "hay_filtros": any(datos.values()),
        },
    )


def pdf_informe(request, pk):
    """Descarga del informe emitido en PDF A4 (US 7.3), desde su copia."""
    informe = get_object_or_404(Informe.objects.select_related("estudio"), estudio__pk=pk)
    try:
        contenido = pdf.generar_pdf(informe)
    except Exception:
        logger.exception("No se pudo generar el PDF del informe %s", informe.numero_mostrado)
        messages.error(request, "No se pudo generar el PDF. Intentá nuevamente.")
        return redirect("informes:ver", pk=pk)
    respuesta = HttpResponse(contenido, content_type="application/pdf")
    respuesta["Content-Disposition"] = f'attachment; filename="{informe.numero_mostrado}.pdf"'
    return respuesta


def imprimir(request, pk):
    """El informe emitido en hoja A4 para imprimir desde el navegador (US 7.3)."""
    informe = get_object_or_404(Informe.objects.select_related("estudio"), estudio__pk=pk)
    contexto = {"informe": informe, "contenido": informe.contenido, "pdf": False}
    return render(request, "informes/impreso.html", contexto)


@permission_required("informes.emitir_informes", raise_exception=True)
def mi_firma(request):
    """Firma y matrícula de quien emite informes (US 7.3); cada uno edita solo la suya."""
    form = FirmaForm(request.POST or None, usuario=request.user)
    if request.method == "POST" and form.is_valid():
        form.guardar()
        messages.success(request, "Se guardó tu firma.")
        return redirect("informes:mi_firma")
    return render(request, "informes/mi_firma.html", {"form": form, "firma": form.actual})
