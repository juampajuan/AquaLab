"""Vistas HTML de gestión, sin escrituras directas de catálogo."""

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core import signing
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from pruebas.models import Prueba

from . import confirmaciones_tipos as tokens
from .forms_tipos import TipoEstudioForm
from .gestion_tipos import (
    PERMISO,
    DatosTipoInvalidos,
    GestionTipoError,
    TipoNoExiste,
    TipoUtilizado,
    VersionTipoDesactualizada,
    gestionar_tipo_estudio,
    leer_tipo_administrativo,
)
from .models import TipoEstudio


def solicitud_invalida(request, error=None):
    messages.error(
        request,
        str(error) if error else "La solicitud no es válida o venció. Iniciá una nueva revisión.",
    )
    return redirect("estudios:tipos_listar")


@permission_required(PERMISO, raise_exception=True)
@require_GET
def tipos_listar(request):
    estado = request.GET.get("estado", "todos")
    tipos = TipoEstudio.objects.annotate(
        cantidad_pruebas=Count("pruebas", distinct=True),
        cantidad_estudios=Count("estudios", distinct=True),
    ).order_by("nombre", "pk")
    if estado in ("activos", "inactivos"):
        tipos = tipos.filter(activo=estado == "activos")
    else:
        estado = "todos"
    return render(
        request,
        "estudios/tipos/lista.html",
        {"page_obj": Paginator(tipos, 20).get_page(request.GET.get("page")), "estado": estado},
    )


@permission_required(PERMISO, raise_exception=True)
@require_http_methods(["GET", "POST"])
def tipos_crear(request):
    contexto = request.POST.get("contexto", "")
    anterior = request.POST.get("anterior", "")
    if request.method == "GET":
        initial = None
        clave = request.GET.get("solicitud")
        if clave:
            borrador = tokens.pendientes(request).get(clave)
            if not borrador or borrador["operacion"] != "crear":
                return solicitud_invalida(request)
            initial = {**borrador["datos"], "pruebas": borrador["datos"]["prueba_ids"]}
            anterior = clave
        form = TipoEstudioForm(initial=initial)
        contexto = tokens.crear_contexto(request, "crear")
    else:
        try:
            tokens.leer_contexto(request, contexto, "crear")
        except signing.BadSignature:
            return solicitud_invalida(request)
        if request.POST.get("cancelar") == "1":
            return cancelar_formulario(request, "crear", None, anterior)
        form = TipoEstudioForm(request.POST)
        if form.is_valid():
            datos = form.datos_servicio()
            resumen = {
                **datos,
                "activo": True,
                "pruebas": list(form.cleaned_data["pruebas"].values("id", "codigo", "nombre")),
            }
            try:
                if anterior and anterior not in tokens.pendientes(request):
                    return solicitud_invalida(request)
                borrador = tokens.preparar(
                    request, "crear", None, None, datos, resumen, anterior=anterior
                )
            except signing.BadSignature as exc:
                return solicitud_invalida(request, exc)
            return redirect(reverse("estudios:tipos_confirmar") + "?solicitud=" + borrador["clave"])
    return render(
        request,
        "estudios/tipos/formulario.html",
        {
            "form": form,
            "contexto": contexto,
            "anterior": anterior,
            "operacion": "crear",
            "sin_pruebas": not Prueba.objects.exists(),
        },
    )


@permission_required(PERMISO, raise_exception=True)
@require_http_methods(["GET", "POST"])
def tipos_confirmar(request):
    try:
        if request.method == "GET":
            borrador = tokens.pendientes(request).get(request.GET.get("solicitud"))
            if not borrador:
                return solicitud_invalida(request)
            tokens.verificar(request, borrador["token"])
        else:
            borrador = tokens.verificar(request, request.POST.get("token", ""))
            accion = request.POST.get("accion")
            if accion == "cancelar":
                tokens.descartar(request, borrador["clave"])
                messages.info(request, "Operación cancelada. No se guardaron cambios.")
                return redirect("estudios:tipos_listar")
            if accion != "confirmar":
                return solicitud_invalida(request)
            try:
                resultado = gestionar_tipo_estudio(
                    usuario=request.user,
                    operacion=borrador["operacion"],
                    tipo_id=borrador["tipo_id"],
                    version_esperada=borrador["version"],
                    datos=borrador["datos"],
                )
            except VersionTipoDesactualizada as exc:
                return mostrar_conflicto(request, borrador["resumen"], exc.configuracion)
            except TipoUtilizado as exc:
                messages.error(request, str(exc))
                return render(
                    request,
                    "estudios/tipos/confirmar.html",
                    {"borrador": borrador, "tipo_utilizado": True},
                )
            except DatosTipoInvalidos as exc:
                return render(
                    request,
                    "estudios/tipos/confirmar.html",
                    {
                        "borrador": borrador,
                        "errores": exc.errores,
                        "volver_url": url_volver(borrador),
                    },
                )
            except GestionTipoError as exc:
                messages.error(request, str(exc))
            else:
                tokens.descartar(request, borrador["clave"])
                messages.success(
                    request,
                    {
                        "creado": "Tipo de estudio creado.",
                        "actualizado": "Tipo de estudio actualizado.",
                        "sin_cambios": "No hubo cambios en el tipo de estudio.",
                        "desactivado": "Tipo de estudio desactivado.",
                        "reactivado": "Tipo de estudio reactivado.",
                        "eliminado": "Tipo de estudio eliminado.",
                    }.get(resultado.estado, "Operación completada."),
                )
                return redirect("estudios:tipos_listar")
    except signing.BadSignature:
        return solicitud_invalida(request)
    return render(
        request,
        "estudios/tipos/confirmar.html",
        {
            "borrador": borrador,
            "volver_url": url_volver(borrador),
        },
    )


def url_volver(borrador):
    if borrador["operacion"] == "crear":
        url = reverse("estudios:tipos_crear")
    elif borrador["operacion"] == "editar":
        url = reverse("estudios:tipos_editar", args=[borrador["tipo_id"]])
    else:
        return None
    return url + "?solicitud=" + borrador["clave"]


def mostrar_conflicto(request, propuesta, actual):
    return render(
        request, "estudios/tipos/conflicto.html", {"propuesta": propuesta, "actual": actual}
    )


@permission_required(PERMISO, raise_exception=True)
@require_http_methods(["GET", "POST"])
def tipos_editar(request, pk):
    try:
        actual = leer_tipo_administrativo(usuario=request.user, tipo_id=pk)
    except TipoNoExiste as exc:
        raise Http404 from exc
    contexto = request.POST.get("contexto", "")
    anterior = request.POST.get("anterior", "")
    if request.method == "GET":
        initial = {**actual, "pruebas": [p["id"] for p in actual["pruebas"]]}
        version = actual["version"]
        clave = request.GET.get("solicitud")
        if clave:
            borrador = tokens.pendientes(request).get(clave)
            if not borrador or borrador["operacion"] != "editar" or borrador["tipo_id"] != pk:
                return solicitud_invalida(request)
            version = borrador["version"]
            initial = {**borrador["datos"], "pruebas": borrador["datos"]["prueba_ids"]}
            anterior = clave
        contexto = tokens.crear_contexto(request, "editar", pk, version)
        form = TipoEstudioForm(initial=initial, tipo_id=pk)
    else:
        try:
            apertura = tokens.leer_contexto(request, contexto, "editar", pk)
        except signing.BadSignature:
            return solicitud_invalida(request)
        if request.POST.get("cancelar") == "1":
            return cancelar_formulario(request, "editar", pk, anterior)
        form = TipoEstudioForm(request.POST, tipo_id=pk)
        # La versión de apertura jamás se reemplaza por la leída en este POST.
        if apertura["version"] != actual["version"]:
            propuesta = {
                "nombre": request.POST.get("nombre", ""),
                "descripcion": request.POST.get("descripcion", ""),
                "pruebas": list(
                    Prueba.objects.filter(
                        pk__in=[
                            v
                            for v in request.POST.getlist("pruebas")
                            if v.isascii() and v.isdigit() and len(v) < 19
                        ]
                    ).values("id", "codigo", "nombre")
                ),
            }
            return mostrar_conflicto(request, propuesta, actual)
        if form.is_valid():
            datos = form.datos_servicio()
            resumen = {
                **datos,
                "activo": actual["activo"],
                "pruebas": list(form.cleaned_data["pruebas"].values("id", "codigo", "nombre")),
            }
            try:
                if anterior and anterior not in tokens.pendientes(request):
                    return solicitud_invalida(request)
                borrador = tokens.preparar(
                    request, "editar", pk, apertura["version"], datos, resumen, anterior=anterior
                )
            except signing.BadSignature as exc:
                return solicitud_invalida(request, exc)
            return redirect(reverse("estudios:tipos_confirmar") + "?solicitud=" + borrador["clave"])
    return render(
        request,
        "estudios/tipos/formulario.html",
        {
            "form": form,
            "contexto": contexto,
            "anterior": anterior,
            "operacion": "editar",
            "actual": actual,
            "sin_pruebas": not Prueba.objects.exists(),
        },
    )


def preparar_operacion(request, pk, operacion):
    try:
        actual = leer_tipo_administrativo(usuario=request.user, tipo_id=pk)
    except TipoNoExiste as exc:
        raise Http404 from exc
    try:
        borrador = tokens.preparar(request, operacion, pk, actual["version"], {}, actual)
    except signing.BadSignature as exc:
        return solicitud_invalida(request, exc)
    errores = {}
    if operacion == "reactivar" and not actual["pruebas"]:
        errores["pruebas"] = "El tipo necesita al menos una prueba válida para reactivarse."
    return render(
        request, "estudios/tipos/confirmar.html", {"borrador": borrador, "errores": errores}
    )


@permission_required(PERMISO, raise_exception=True)
@require_GET
def tipos_desactivar(request, pk):
    return preparar_operacion(request, pk, "desactivar")


@permission_required(PERMISO, raise_exception=True)
@require_GET
def tipos_reactivar(request, pk):
    return preparar_operacion(request, pk, "reactivar")


@permission_required(PERMISO, raise_exception=True)
@require_GET
def tipos_eliminar(request, pk):
    return preparar_operacion(request, pk, "eliminar")


def cancelar_formulario(request, operacion, tipo_id, anterior):
    if anterior:
        borrador = tokens.pendientes(request).get(anterior)
        if not borrador or (borrador["operacion"], borrador["tipo_id"]) != (operacion, tipo_id):
            return solicitud_invalida(request)
        try:
            tokens.verificar(request, borrador["token"])
        except signing.BadSignature:
            return solicitud_invalida(request)
        tokens.descartar(request, anterior)
    messages.info(request, "Operación cancelada. No se guardaron cambios.")
    return redirect("estudios:tipos_listar")
