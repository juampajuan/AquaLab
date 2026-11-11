import logging
import uuid
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from estudios import calculo, desvios
from estudios.forms import BuscarEstudioForm, ElegirOrigenForm
from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Estudio
from estudios.views import RESULTADOS_POR_PAGINA

from . import calidad, envios, pdf, servicios, tablero
from .busqueda import informes_emitidos
from .contenido import armar_contenido
from .forms import BuscarInformeForm, FirmaForm
from .models import FirmaProfesional, Informe, ResultadoEnvio
from .servicios import EmitirInformeError, InformeNoDisponible

logger = logging.getLogger("informes")


def listar(request):
    """Estudios por informar (SCRUM-82): solo los que se pueden informar ya.

    Los que están sin iniciar o en proceso no se pueden informar, y los que ya tienen informe se
    buscan en «Informes emitidos»; por eso no se listan.
    """
    page_obj = None
    q = ""
    form = BuscarEstudioForm(request.GET or None)
    if not form.is_bound or form.is_valid():
        q = form.cleaned_data.get("q", "") if form.is_bound else ""
        qs = servicios.estudios_para_informar(q, solo_listos=True)
        page_obj = Paginator(qs, RESULTADOS_POR_PAGINA).get_page(request.GET.get("page"))
    return render(
        request,
        "informes/listar.html",
        {"form": form, "page_obj": page_obj, "q": q, "parametros": urlencode({"q": q})},
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


def enlaces_del_informe(estudio):
    """En pantalla, el estudio, la muestra y el cliente del informe son enlaces (no en el PDF).

    Llevan `?desde=informe` para que el «Volver» de esas fichas regrese al informe.
    """
    cliente = estudio.muestra.cliente
    enlaces = {
        "estudio": reverse("estudios:detalle", args=[estudio.pk]),
        "muestra": reverse("muestras:detalle", args=[estudio.muestra.pk]),
        "cliente": reverse("clientes:detalle", args=[cliente.pk]) if cliente.activo else "",
    }
    return {clave: f"{url}?desde=informe" if url else "" for clave, url in enlaces.items()}


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
    # Se llega desde «Estudios por informar» (?desde=listos) o desde la ficha del estudio: «Volver»
    # lleva a donde se estaba (SCRUM-82). Cualquier otro valor vuelve al estudio.
    if request.GET.get("desde") == "listos":
        volver_url = reverse("informes:listar")
    else:
        volver_url = reverse("estudios:detalle", args=[estudio.pk])
    contexto = {
        "estudio": estudio,
        "volver_url": volver_url,
        "contenido": armar_contenido(estudio, request.user),
        "enlaces": enlaces_del_informe(estudio),
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
        Informe.objects.select_related("estudio__muestra__cliente", "emitido_por"), estudio__pk=pk
    )
    estudio = informe.estudio
    cliente = estudio.muestra.cliente
    # «Volver» lleva a donde se estaba (SCRUM-82): informes emitidos, el historial del cliente o,
    # por defecto, el estudio.
    desde = request.GET.get("desde")
    if desde == "emitidos":
        volver_url = reverse("informes:emitidos")
    elif desde == "historial" and cliente.activo:
        volver_url = reverse("clientes:historial", args=[cliente.pk])
    else:
        volver_url = reverse("estudios:detalle", args=[estudio.pk])
    contexto = {
        "estudio": estudio,
        "informe": informe,
        "contenido": informe.contenido,
        "envios": list(informe.envios.select_related("enviado_por")),
        "volver_url": volver_url,
        "enlaces": enlaces_del_informe(estudio),
    }
    return render(request, "informes/ver.html", contexto)


@permission_required("informes.emitir_informes", raise_exception=True)
@require_http_methods(["GET", "POST"])
def enviar(request, pk):
    """Envío del informe al correo del cliente (SCRUM-79): confirmación (GET) y envío (POST).

    `PermissionDenied` y `Http404` del servicio no se atrapan: Django responde 403 y 404.
    """
    informe = get_object_or_404(
        Informe.objects.select_related("estudio__muestra__cliente"), estudio__pk=pk
    )
    if request.method == "GET":
        contexto = {
            "estudio": informe.estudio,
            "informe": informe,
            "cliente": informe.estudio.muestra.cliente,
            "ultimo": envios.ultimo_envio_exitoso(informe),
            "clave": uuid.uuid4(),
        }
        return render(request, "informes/enviar_confirmar.html", contexto)
    try:
        clave = uuid.UUID(request.POST.get("clave", ""))
    except ValueError:
        messages.error(request, "La confirmación no es válida. Volvé a intentarlo.")
        return redirect("informes:enviar", pk=pk)
    try:
        resultado = envios.enviar_informe(pk, request.user, clave)
    except DatabaseError:
        logger.exception("No se pudo registrar el envío del informe %s", informe.numero_mostrado)
        messages.error(request, "No se pudo registrar el envío. Intentá nuevamente.")
        return redirect("informes:ver", pk=pk)
    envio = resultado.envio
    if resultado.duplicado:
        messages.info(
            request,
            f"El informe {informe.numero_mostrado} ya se había enviado con esta confirmación.",
        )
    elif envio.resultado == ResultadoEnvio.ENVIADO:
        messages.success(
            request, f"Se envió el informe {informe.numero_mostrado} a {envio.destinatario}."
        )
    else:
        messages.error(
            request,
            f"No se pudo enviar el informe a {envio.destinatario}. Intentá nuevamente.",
        )
    return redirect("informes:ver", pk=pk)


def emitidos(request):
    """Listado y búsqueda de informes emitidos (US 7.3): cualquier empleado con sesión."""
    page_obj = None
    form = BuscarInformeForm(request.GET or None)
    datos = {"q": "", "desde": None, "hasta": None, "envio": ""}
    if form.is_bound and form.is_valid():
        datos = form.cleaned_data
    if not form.is_bound or form.is_valid():
        qs = informes_emitidos(datos["q"], datos["desde"], datos["hasta"], datos["envio"])
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


@permission_required("informes.ver_dashboard", raise_exception=True)
@require_GET
def dashboard(request):
    """Indicadores del laboratorio (US 8.3): solo con el permiso «Puede ver el dashboard»."""
    contexto = tablero.armar(request.GET.get("periodo", "este_mes"))
    contexto["calidad"] = calidad.armar(contexto["periodo"])  # sección «Calidad» (US 8.4)
    contexto["datos_graficos"].update(contexto["calidad"]["graficos"])
    contexto["form_origen"] = ElegirOrigenForm()  # comparación histórica (US 8.1)
    pendientes = desvios.pendientes()  # desvíos sin revisar (US 8.2), no dependen del período
    contexto["desvios_cantidad"] = len(pendientes)
    contexto["desvios_recientes"] = pendientes[:10]
    contexto["regla_desvio"] = desvios.texto_regla(desvios.regla())
    return render(request, "informes/dashboard.html", contexto)
