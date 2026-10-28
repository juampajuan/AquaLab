from django.contrib import messages
from django.core import signing
from django.db import DatabaseError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import format_html

from muestras.models import Muestra

from . import servicios
from .catalogo import CatalogoNoDisponible
from .confirmaciones import cargar_token, descartar, pendientes, preparar
from .forms import AgregarPruebaForm, CrearEstudioForm
from .models import Estudio
from .servicios import (
    CrearEstudioError,
    GestionPruebasError,
    PruebaYaAsignada,
    VersionDesactualizada,
    comprobar_identidad,
    crear_estudio,
)

MENSAJE_NO_MODIFICABLE = "Este estudio ya no admite cambios en sus pruebas."


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


def detalle(request, pk):
    estudio = get_object_or_404(
        Estudio.objects.select_related("muestra__cliente", "muestra__origen", "creado_por"), pk=pk
    )
    asignaciones = estudio.pruebas_asignadas.select_related("prueba").order_by("prueba__codigo")
    return render(
        request, "estudios/detalle.html", {"estudio": estudio, "asignaciones": asignaciones}
    )


def formulario_prueba(request, estudio, form):
    return render(request, "estudios/agregar_prueba.html", {"estudio": estudio, "form": form})


def agregar_prueba(request, pk):
    estudio = get_object_or_404(Estudio.objects.select_related("muestra"), pk=pk)
    volver = redirect("estudios:detalle", pk=estudio.pk)
    if not estudio.admite_modificaciones:
        messages.error(request, MENSAJE_NO_MODIFICABLE)
        return volver
    if request.method != "POST":
        form = AgregarPruebaForm(estudio=estudio)
        return formulario_prueba(request, estudio, form)
    accion = request.POST.get("accion")
    if accion not in ("revisar", "confirmar"):
        messages.error(request, "La acción no es válida.")
        return volver
    form = AgregarPruebaForm(request.POST, estudio=estudio)
    if not form.is_valid():
        # Un reenvío de una confirmación ya aplicada se informa como aviso, no como error.
        enviada = request.POST.get("prueba", "")
        asignada = (
            estudio.pruebas_asignadas.select_related("prueba").filter(prueba_id=enviada).first()
            if accion == "confirmar" and enviada.isdigit()
            else None
        )
        if asignada:
            codigo = asignada.prueba.codigo
            messages.info(request, f"La prueba {codigo} ya forma parte del estudio.")
            return volver
        return formulario_prueba(request, estudio, form)
    prueba = form.cleaned_data["prueba"]
    if accion == "revisar":
        contexto = {"estudio": estudio, "prueba": prueba}
        return render(request, "estudios/agregar_prueba_confirmar.html", contexto)
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
    return volver


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
        form = CrearEstudioForm(initial=b["datos"] if b else None)
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
