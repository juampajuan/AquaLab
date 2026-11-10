"""Pantallas de gestión del catálogo (SCRUM-73), bajo «Administración».

Solo arman formularios, resúmenes y mensajes: toda escritura pasa por `gestion.gestionar_prueba`,
que revalida las reglas. Acceso: grupo «Administradores» + permiso del panel (403 al resto).
"""

from django.contrib import messages
from django.core import signing
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from usuarios.permisos_administracion import administracion_requerida

from . import confirmaciones as tokens
from . import gestion
from .formularios import PruebaForm
from .models import Prueba, TipoCalculo, referencias_formula

ETIQUETAS = {
    "codigo": "Código",
    "nombre": "Nombre",
    "tipo_calculo": "Tipo de cálculo",
    "formula": "Fórmula",
    "unidad_medicion": "Unidad de medición",
    "unidad": "Unidad del resultado",
    "limite_min": "Límite mínimo",
    "limite_max": "Límite máximo",
    "norma": "Norma",
    "limite_deteccion": "Límite de detección",
    "cloacal_limite_min": "Mínimo cloacal",
    "cloacal_limite_max": "Máximo cloacal",
    "cloacal_norma": "Norma cloacal",
    "canal_limite_min": "Mínimo canal",
    "canal_limite_max": "Máximo canal",
    "canal_norma": "Norma canal",
    "observacion": "Observación",
}
MENSAJES = {
    "creada": "Prueba creada.",
    "actualizada": "Prueba actualizada.",
    "sin_cambios": "No hubo cambios.",
    "desactivada": "Prueba desactivada.",
    "reactivada": "Prueba reactivada.",
    "eliminada": "Prueba eliminada.",
}


def solicitud_invalida(request, error=None):
    messages.error(
        request,
        str(error) if error else "La solicitud no es válida o venció. Iniciá una nueva revisión.",
    )
    return redirect("administracion:pruebas")


def prueba_o_404(pk):
    return get_object_or_404(Prueba.objects.select_related("creada_por", "modificada_por"), pk=pk)


def filas_resumen(datos, antes=None):
    filas = []
    for campo, etiqueta in ETIQUETAS.items():
        valor = datos.get(campo, "")
        if campo == "tipo_calculo":
            valor = TipoCalculo(valor).label if valor in TipoCalculo.values else valor
        anterior = None
        if antes is not None:
            anterior = antes.get(campo, "")
            if campo == "tipo_calculo" and anterior in TipoCalculo.values:
                anterior = TipoCalculo(anterior).label
        filas.append(
            {
                "etiqueta": etiqueta,
                "valor": valor,
                "anterior": anterior,
                "cambia": antes is not None and anterior != valor,
            }
        )
    return filas


@administracion_requerida
@require_GET
def ficha(request, pk):
    prueba = prueba_o_404(pk)
    en_uso = prueba.esta_en_uso()
    return render(
        request,
        "pruebas/ficha.html",
        {
            "prueba": prueba,
            "en_uso": en_uso,
            "mensaje_en_uso": gestion.MENSAJE_EN_USO,
            "dependientes": gestion.dependientes(prueba),
            "usa_inactivas": gestion.dependencias_inactivas().get(prueba.pk, []),
            "limites_vertido": prueba.limites_vertido.order_by("tipo_vertido"),
        },
    )


def formulario(request, operacion, prueba=None):
    pk = prueba.pk if prueba else None
    bloquear = bool(prueba and prueba.esta_en_uso())
    initial = gestion.datos_de(prueba) if prueba else None
    contexto = request.POST.get("contexto", "")
    anterior = request.POST.get("anterior", "")
    if request.method == "GET":
        version = prueba.version if prueba else None
        clave = request.GET.get("solicitud")
        if clave:
            borrador = tokens.pendientes(request).get(clave)
            if not borrador or (borrador["operacion"], borrador["prueba_id"]) != (operacion, pk):
                return solicitud_invalida(request)
            initial, version, anterior = borrador["datos"], borrador["version"], clave
        contexto = tokens.crear_contexto(request, operacion, pk, version)
        form = PruebaForm(initial=initial, prueba=prueba, bloquear_metodo=bloquear)
    else:
        try:
            apertura = tokens.leer_contexto(request, contexto, operacion, pk)
        except signing.BadSignature:
            return solicitud_invalida(request)
        if request.POST.get("cancelar") == "1":
            if anterior:
                tokens.descartar(request, anterior)
            messages.info(request, "Operación cancelada. No se guardaron cambios.")
            return redirect("catalogo:ficha", pk) if pk else redirect("administracion:pruebas")
        if prueba and apertura["version"] != prueba.version:
            messages.error(request, gestion.MENSAJE_VERSION)
            return redirect("catalogo:ficha", pk)
        form = PruebaForm(request.POST, initial=initial, prueba=prueba, bloquear_metodo=bloquear)
        if form.is_valid():
            try:
                borrador = tokens.preparar(
                    request,
                    operacion,
                    pk,
                    apertura["version"],
                    form.datos_servicio(),
                    anterior=anterior,
                )
            except signing.BadSignature as exc:
                return solicitud_invalida(request, exc)
            return redirect(reverse("catalogo:confirmar") + "?solicitud=" + borrador["clave"])
    return render(
        request,
        "pruebas/formulario.html",
        {
            "form": form,
            "prueba": prueba,
            "operacion": operacion,
            "contexto": contexto,
            "anterior": anterior,
            "bloqueada": bloquear,
            "mensaje_en_uso": gestion.MENSAJE_EN_USO,
        },
    )


@administracion_requerida
@require_http_methods(["GET", "POST"])
def nueva(request):
    return formulario(request, "crear")


@administracion_requerida
@require_http_methods(["GET", "POST"])
def editar(request, pk):
    return formulario(request, "editar", prueba_o_404(pk))


def preparar_operacion(request, pk, operacion):
    prueba = prueba_o_404(pk)
    if operacion == "eliminar":
        motivo = None
        if prueba.esta_en_uso():
            motivo = (
                "Esta prueba ya se usa en tipos de estudio o estudios: no se puede eliminar, solo "
                "desactivar."
            )
        elif usan := gestion.dependientes(prueba):
            motivo = str(gestion.PruebaReferenciada([p.codigo for p in usan]))
        if motivo:
            messages.error(request, motivo)
            return redirect("catalogo:ficha", pk)
    try:
        borrador = tokens.preparar(request, operacion, pk, prueba.version, {})
    except signing.BadSignature as exc:
        return solicitud_invalida(request, exc)
    return redirect(reverse("catalogo:confirmar") + "?solicitud=" + borrador["clave"])


@administracion_requerida
@require_GET
def desactivar(request, pk):
    return preparar_operacion(request, pk, "desactivar")


@administracion_requerida
@require_GET
def reactivar(request, pk):
    return preparar_operacion(request, pk, "reactivar")


@administracion_requerida
@require_GET
def eliminar(request, pk):
    return preparar_operacion(request, pk, "eliminar")


def contexto_confirmacion(borrador, errores=None):
    prueba = None
    if borrador["prueba_id"] is not None:
        prueba = Prueba.objects.filter(pk=borrador["prueba_id"]).first()
        if prueba is None:
            raise Http404
    operacion = borrador["operacion"]
    contexto = {"borrador": borrador, "prueba": prueba, "errores": errores or {}}
    if operacion in ("crear", "editar"):
        antes = gestion.datos_de(prueba) if prueba else None
        contexto["filas"] = filas_resumen(borrador["datos"], antes)
        url = (
            reverse("catalogo:nueva")
            if operacion == "crear"
            else reverse("catalogo:editar", args=[prueba.pk])
        )
        contexto["volver_url"] = url + "?solicitud=" + borrador["clave"]
    if operacion == "desactivar":
        contexto["dependientes"] = gestion.dependientes(prueba, solo_activas=True)
        contexto["tipos"] = gestion.tipos_afectados(prueba)
        contexto["candidatas"] = gestion.candidatas_reemplazo(prueba)
    if operacion == "reactivar":
        contexto["usa_inactivas"] = sorted(
            Prueba.objects.filter(
                codigo__in=referencias_formula(prueba.formula), activa=False
            ).values_list("codigo", flat=True)
        )
    return contexto


@administracion_requerida
@require_http_methods(["GET", "POST"])
def confirmar(request):
    try:
        if request.method == "GET":
            borrador = tokens.pendientes(request).get(request.GET.get("solicitud"))
            if not borrador:
                return solicitud_invalida(request)
            tokens.verificar(request, borrador["token"])
            return render(request, "pruebas/confirmar.html", contexto_confirmacion(borrador))
        borrador = tokens.verificar(request, request.POST.get("token", ""))
    except signing.BadSignature:
        return solicitud_invalida(request)
    accion = request.POST.get("accion")
    if accion == "cancelar":
        tokens.descartar(request, borrador["clave"])
        messages.info(request, "Operación cancelada. No se guardaron cambios.")
        if borrador["prueba_id"]:
            return redirect("catalogo:ficha", borrador["prueba_id"])
        return redirect("administracion:pruebas")
    if accion != "confirmar":
        return solicitud_invalida(request)
    try:
        resultado = gestion.gestionar_prueba(
            usuario=request.user,
            operacion=borrador["operacion"],
            prueba_id=borrador["prueba_id"],
            version_esperada=borrador["version"],
            datos=borrador["datos"],
            reemplazo_id=request.POST.get("reemplazo") or None,
        )
    except gestion.DatosInvalidos as exc:
        return render(
            request, "pruebas/confirmar.html", contexto_confirmacion(borrador, exc.errores)
        )
    except gestion.GestionPruebaError as exc:
        tokens.descartar(request, borrador["clave"])
        messages.error(request, str(exc))
        if borrador["prueba_id"] and Prueba.objects.filter(pk=borrador["prueba_id"]).exists():
            return redirect("catalogo:ficha", borrador["prueba_id"])
        return redirect("administracion:pruebas")
    tokens.descartar(request, borrador["clave"])
    if resultado.estado == "reemplazada":
        messages.success(request, f"Prueba desactivada y reemplazada por {resultado.reemplazo}.")
    else:
        messages.success(request, MENSAJES.get(resultado.estado, "Operación completada."))
    if resultado.estado == "eliminada":
        return redirect("administracion:pruebas")
    return redirect("catalogo:ficha", resultado.prueba_id)
