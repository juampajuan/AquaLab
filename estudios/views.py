from django.contrib import messages
from django.core import signing
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import format_html

from clientes.models import normalizar_numero_documento
from muestras.models import Muestra

from . import servicios
from .catalogo import CatalogoNoDisponible
from .confirmaciones import cargar_token, descartar, pendientes, preparar
from .forms import AgregarPruebaForm, BuscarEstudioForm, CrearEstudioForm
from .models import EstadoPruebaEstudio, Estudio
from .servicios import (
    CrearEstudioError,
    GestionPruebasError,
    PruebaYaAsignada,
    PruebaYaQuitada,
    VersionDesactualizada,
    comprobar_identidad,
    crear_estudio,
)

RESULTADOS_POR_PAGINA = 20
MAX_NUMERO_PI_SQL = 2_147_483_647


def exito(request, estudio):
    descartar(request, estudio.clave_idempotencia)
    messages.success(
        request,
        format_html(
            '<a href="{}">Estudio {}</a> creado para la muestra PI {}.',
            reverse("estudios:detalle", args=[estudio.pk]),
            estudio.pk,
            estudio.muestra.numero_pi,
        ),
    )
    return redirect("estudios:crear")


def resumen(request, borrador, *, recuperar=False):
    return render(
        request, "estudios/crear_confirmar.html", {"borrador": borrador, "recuperar": recuperar}
    )


def crear(request):
    anterior = request.GET.get("volver", "")
    if request.method == "POST":
        form = CrearEstudioForm(request.POST)
        anterior = request.POST.get("anterior", "")
        if form.is_valid():
            try:
                b = preparar(request, form.cleaned_data["muestra"], form.cleaned_data["tipo"].pk)
            except (CatalogoNoDisponible, CrearEstudioError) as exc:
                form.add_error("tipo", str(exc))
            except DatabaseError:
                form.add_error(None, "No se pudo preparar el estudio. Intentá nuevamente.")
            else:
                if anterior:
                    descartar(request, anterior)
                return redirect(f"{reverse('estudios:confirmar')}?solicitud={b['datos']['clave']}")
    else:
        b = pendientes(request).get(anterior)
        if b:
            initial = b["datos"]
        elif request.GET.get("muestra"):
            initial = {"muestra": request.GET.get("muestra")}
        else:
            initial = None
        form = CrearEstudioForm(initial=initial)
    return render(request, "estudios/crear_form.html", {"form": form, "anterior": anterior})


def confirmar(request):
    if request.method != "POST":
        b = pendientes(request).get(request.GET.get("solicitud", ""))
        return resumen(request, b) if b else redirect("estudios:crear")
    accion = request.POST.get("accion")
    if accion not in ("confirmar", "cancelar", "recuperar"):
        messages.error(request, "La acción no es válida.")
        return redirect("estudios:crear")
    token = request.POST.get("token", "")
    try:
        datos = cargar_token(request, token, recuperar=accion in ("cancelar", "recuperar"))
    except signing.SignatureExpired:
        messages.warning(request, "La confirmación venció. Recuperá la solicitud para revisarla.")
        return resumen(request, {"token": token}, recuperar=True)
    except (signing.BadSignature, CrearEstudioError, TypeError, ValueError):
        messages.error(request, "La confirmación no es válida para esta sesión.")
        return redirect("estudios:crear")
    b = pendientes(request).get(datos["clave"])
    if accion == "cancelar":
        descartar(request, datos["clave"])
        messages.info(request, "Creación de estudio cancelada.")
        return redirect("estudios:crear")
    try:
        if accion == "recuperar":
            existente = Estudio.objects.filter(clave_idempotencia=datos["clave"]).first()
            if existente:
                return exito(request, comprobar_identidad(existente, datos, request.user))
            if not b:
                raise CrearEstudioError("La solicitud ya no está pendiente.")
            muestra = Muestra.objects.select_related("cliente", "origen").get(pk=datos["muestra"])
            return resumen(request, preparar(request, muestra, datos["tipo"], clave=datos["clave"]))
        estudio = crear_estudio(datos, request.user, pendiente=b is not None)
    except VersionDesactualizada as exc:
        muestra = (
            Muestra.objects.select_related("cliente", "origen").filter(pk=datos["muestra"]).first()
        )
        if not b or muestra is None:
            messages.error(request, "La solicitud no está disponible.")
            return redirect("estudios:crear")
        messages.warning(request, str(exc))
        return resumen(
            request,
            preparar(
                request, muestra, datos["tipo"], clave=datos["clave"], config=exc.configuracion
            ),
        )
    except (CrearEstudioError, CatalogoNoDisponible, Muestra.DoesNotExist) as exc:
        messages.error(
            request,
            str(exc)
            if not isinstance(exc, Muestra.DoesNotExist)
            else "La muestra no está disponible.",
        )
        return redirect("estudios:crear")
    except DatabaseError:
        messages.error(request, "No se pudo crear el estudio. Intentá nuevamente.")
        return resumen(request, b) if b else redirect("estudios:crear")
    return exito(request, estudio)


def buscar(request):
    page_obj = None
    q = ""
    form = BuscarEstudioForm(request.GET or None)
    if not form.is_bound or form.is_valid():
        q = form.cleaned_data.get("q", "") if form.is_bound else ""
        qs = Estudio.objects.select_related(
            "muestra", "muestra__cliente", "muestra__origen"
        ).order_by(*Estudio._meta.ordering)
        if q:
            filtro = (
                Q(muestra__nombre__unaccent__icontains=q)
                | Q(muestra__cliente__nombre__unaccent__icontains=q)
                | Q(muestra__cliente__razon_social__unaccent__icontains=q)
                | Q(tipo_nombre_snapshot__unaccent__icontains=q)
            )
            if q.isascii() and q.isdigit():
                numero = int(q)
                filtro |= Q(pk=numero)
                if numero <= MAX_NUMERO_PI_SQL:
                    filtro |= Q(muestra__numero_pi=numero)
            q_doc = normalizar_numero_documento(q)
            if len(q_doc) >= 4 and q_doc.isascii() and q_doc.isdigit():
                filtro |= Q(muestra__cliente__numero_documento__contains=q_doc)
            qs = qs.filter(filtro)
        page_obj = Paginator(qs, RESULTADOS_POR_PAGINA).get_page(request.GET.get("page"))
    return render(
        request,
        "estudios/buscar.html",
        {"form": form, "page_obj": page_obj, "q": q},
    )


def detalle(request, pk):
    estudio = get_object_or_404(
        Estudio.objects.select_related(
            "muestra", "muestra__cliente", "muestra__origen", "creado_por"
        ),
        pk=pk,
    )
    pruebas_asignadas = list(
        estudio.pruebas_asignadas.select_related("prueba").order_by("prueba__codigo", "pk")
    )
    total_pruebas = len(pruebas_asignadas)
    pruebas_completadas = sum(
        1 for a in pruebas_asignadas if a.estado == EstadoPruebaEstudio.COMPLETADA
    )
    pruebas_cargadas = sum(1 for a in pruebas_asignadas if a.estado == EstadoPruebaEstudio.CARGADA)
    pruebas_pendientes = sum(
        1 for a in pruebas_asignadas if a.estado == EstadoPruebaEstudio.PENDIENTE
    )
    return render(
        request,
        "estudios/detalle.html",
        {
            "estudio": estudio,
            "pruebas_asignadas": pruebas_asignadas,
            "total_pruebas": total_pruebas,
            "pruebas_completadas": pruebas_completadas,
            "pruebas_cargadas": pruebas_cargadas,
            "pruebas_pendientes": pruebas_pendientes,
        },
    )


def agregar_prueba(request, pk):
    estudio = get_object_or_404(Estudio.objects.select_related("muestra"), pk=pk)
    contexto = {"estudio": estudio}
    accion = request.POST.get("accion") if request.method == "POST" else None
    if accion != "confirmar" and not estudio.admite_modificaciones:
        # Al confirmar, la regla la revalida el servicio con el estudio bloqueado.
        messages.error(request, "Este estudio ya no admite cambios en sus pruebas.")
        return redirect("estudios:detalle", pk=estudio.pk)
    if request.method != "POST":
        form = AgregarPruebaForm(estudio=estudio)
        return render(request, "estudios/agregar_prueba.html", {**contexto, "form": form})
    if accion not in ("revisar", "confirmar"):
        messages.error(request, "La acción no es válida.")
        return redirect("estudios:detalle", pk=estudio.pk)
    form = AgregarPruebaForm(request.POST, estudio=estudio)
    if form.is_valid():
        prueba = form.cleaned_data["prueba"]
    elif accion == "confirmar" and (prueba := form.prueba_ya_asignada()):
        pass  # Reenvío: el servicio informa que ya forma parte del estudio.
    else:
        return render(request, "estudios/agregar_prueba.html", {**contexto, "form": form})
    if accion == "revisar":
        return render(
            request, "estudios/agregar_prueba_confirmar.html", {**contexto, "prueba": prueba}
        )
    try:
        servicios.agregar_prueba(estudio.pk, prueba.pk, request.user)
    except PruebaYaAsignada as exc:
        messages.info(request, str(exc))
    except GestionPruebasError as exc:
        messages.error(request, str(exc))
    except DatabaseError:
        messages.error(request, "No se pudo agregar la prueba. Intentá nuevamente.")
    else:
        messages.success(request, f"Prueba {prueba} agregada al estudio {estudio.pk}.")
    return redirect("estudios:detalle", pk=estudio.pk)


def quitar_prueba(request, pk, asignacion_pk):
    estudio = get_object_or_404(Estudio.objects.select_related("muestra"), pk=pk)
    if request.method != "POST":
        asignacion = (
            estudio.pruebas_asignadas.select_related("prueba").filter(pk=asignacion_pk).first()
        )
        if asignacion is None:
            messages.info(request, "La prueba ya no forma parte del estudio.")
            return redirect("estudios:detalle", pk=estudio.pk)
        if motivo := servicios.motivo_para_no_quitar(estudio, asignacion):
            messages.error(request, str(motivo))
            return redirect("estudios:detalle", pk=estudio.pk)
        return render(
            request,
            "estudios/quitar_prueba_confirmar.html",
            {"estudio": estudio, "asignacion": asignacion},
        )
    try:
        prueba = servicios.quitar_prueba(estudio.pk, asignacion_pk, request.user)
    except PruebaYaQuitada as exc:
        messages.info(request, str(exc))
    except GestionPruebasError as exc:
        messages.error(request, str(exc))
    except DatabaseError:
        messages.error(request, "No se pudo quitar la prueba. Intentá nuevamente.")
    else:
        messages.success(request, f"Prueba {prueba} quitada del estudio {estudio.pk}.")
    return redirect("estudios:detalle", pk=estudio.pk)
