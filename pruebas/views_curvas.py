"""Pantallas de las curvas de calibración (US 6.6; specs/037-curva-calibracion/contracts).

La carga y la confirmación son del panel de administración (`catalogo:`); las reglas viven en
`pruebas/curvas.py` y los servicios revalidan el permiso. El borrador de la confirmación es el de
`confirmaciones.py` con la operación «curva»; su clave es la `clave` de la curva (doble envío).
"""

from django.contrib import messages
from django.core import signing
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from usuarios.permisos_administracion import administracion_requerida

from . import confirmaciones as tokens
from . import curvas, gestion
from . import importacion_curvas as importacion
from .formularios_curvas import (
    PREFIJO,
    CurvaForm,
    ElegirColumnasForm,
    ImportarForm,
    PuntoFormSet,
    filas_enviadas,
    firmar_archivo,
    formset_con,
)
from .models import CurvaCalibracion, Prueba, TipoCalculo

OPERACION = "curva"
CLAVE_TABLA = "pruebas_curva_tabla"


numero = curvas.texto_numero


def resumen_ajuste(ajuste, unidad):
    return {
        "pendiente": curvas.texto_coeficiente(ajuste.pendiente),
        "ordenada": curvas.texto_coeficiente(ajuste.ordenada),
        "r2": curvas.texto_r2(ajuste.r2),
        "r2_bajo": ajuste.r2_bajo,
        "rango": (
            f"{numero(ajuste.concentracion_min)} a {numero(ajuste.concentracion_max)} {unidad}"
        ),
    }


def datos_grafico(puntos, ajuste, unidad):
    """Datos del json_script «datos-curva»: los puntos y los extremos de la recta como textos."""
    recta = None
    if ajuste:
        desde, hasta = ajuste.concentracion_min, ajuste.concentracion_max
        recta = {
            "desde": {
                "concentracion": str(desde),
                "absorbancia": str(ajuste.pendiente * desde + ajuste.ordenada),
            },
            "hasta": {
                "concentracion": str(hasta),
                "absorbancia": str(ajuste.pendiente * hasta + ajuste.ordenada),
            },
        }
    return {
        "unidad": unidad,
        "puntos": [{"concentracion": str(c), "absorbancia": str(a)} for c, a in puntos],
        "recta": recta,
    }


def prueba_por_curva(pk):
    prueba = get_object_or_404(Prueba, pk=pk)
    return prueba if prueba.tipo_calculo == TipoCalculo.CURVA else None


def no_es_por_curva(request, pk):
    messages.error(request, str(curvas.NoEsPruebaPorCurva()))
    return redirect("catalogo:ficha", pk)


def borrador_invalido(request, pk):
    messages.error(request, curvas.MENSAJE_BORRADOR_INVALIDO)
    return redirect("catalogo:ficha", pk)


def borrador_de(request, clave, pk):
    borrador = tokens.pendientes(request).get(clave or "")
    if not borrador or (borrador["operacion"], borrador["prueba_id"]) != (OPERACION, pk):
        return None
    return borrador


@administracion_requerida
@require_http_methods(["GET", "POST"])
def nueva_curva(request, pk):
    prueba = prueba_por_curva(pk)
    if prueba is None:
        return no_es_por_curva(request, pk)
    contexto = {"prueba": prueba, "prefijo": PREFIJO, "importar": ImportarForm()}
    if request.method == "GET":
        inicial, filas = {}, []
        if clave := request.GET.get("solicitud"):
            borrador = borrador_de(request, clave, prueba.pk)
            if borrador is None:
                return borrador_invalido(request, prueba.pk)
            datos = borrador["datos"]
            inicial = {c: datos.get(c, "") for c in ("fecha_preparacion", "observacion")}
            inicial["archivo_origen"] = firmar_archivo(datos.get("archivo_origen", ""))
            filas = [tuple(p) for p in datos.get("puntos", [])]
        else:
            from django.utils import timezone

            inicial = {"fecha_preparacion": timezone.localdate()}
        contexto.update(form=CurvaForm(initial=inicial), formset=formset_con(filas))
        return render(request, "pruebas/curvas/formulario.html", contexto)

    accion = request.POST.get("accion", "")
    if accion in ("importar", "elegir_columnas"):
        return importar(request, prueba, accion, contexto)
    if accion == "agregar_fila" or accion.startswith("quitar_"):
        filas = filas_enviadas(request.POST)
        if accion == "agregar_fila" and len(filas) < curvas.MAXIMO_PUNTOS:
            filas.append(("", ""))
        elif accion.startswith("quitar_"):
            try:
                filas.pop(int(accion.removeprefix("quitar_")))
            except (ValueError, IndexError):
                pass
        contexto.update(form=form_sin_enviar(request), formset=formset_con(filas))
        return render(request, "pruebas/curvas/formulario.html", contexto)

    form = CurvaForm(request.POST)
    formset = PuntoFormSet(request.POST, prefix=PREFIJO)
    contexto.update(form=form, formset=formset)
    validos = form.is_valid() & formset.is_valid()  # los dos, para mostrar todos los errores
    if not validos:
        return render(request, "pruebas/curvas/formulario.html", contexto)
    # «Calcular recta» lleva directo al resumen, que muestra la recta, el R² y el gráfico.
    if accion in ("calcular", "guardar"):
        datos = {
            "fecha_preparacion": form.cleaned_data["fecha_preparacion"].isoformat(),
            "observacion": form.cleaned_data["observacion"].strip(),
            "archivo_origen": form.cleaned_data["archivo_origen"].strip(),
            "puntos": formset.textos(),
        }
        try:
            borrador = tokens.preparar(request, OPERACION, prueba.pk, None, datos)
        except signing.BadSignature as exc:
            messages.error(request, str(exc))
            return redirect("catalogo:ficha", prueba.pk)
        url = reverse("catalogo:confirmar_curva", args=[prueba.pk])
        return redirect(f"{url}?solicitud={borrador['clave']}")
    contexto.update(
        ajuste=resumen_ajuste(formset.ajuste, prueba.unidad),
        grafico=datos_grafico(formset.puntos, formset.ajuste, prueba.unidad),
    )
    return render(request, "pruebas/curvas/formulario.html", contexto)


def resumen_pendientes(prueba):
    """«N mediciones en M estudios esperan curva» (FR-025), o "" si no hay ninguna."""
    pendientes = curvas.pendientes_de_curva(prueba=prueba)
    if not pendientes:
        return ""
    estudios = len({a.estudio_id for a in pendientes})
    mediciones = "1 medición" if len(pendientes) == 1 else f"{len(pendientes)} mediciones"
    en = "1 estudio" if estudios == 1 else f"{estudios} estudios"
    verbo = "espera" if len(pendientes) == 1 else "esperan"
    return f"{mediciones} en {en} {verbo} curva"


def form_sin_enviar(request, **cambios):
    """El formulario de la curva con lo que se escribió (sin validar) y los `cambios`."""
    inicial = {c: request.POST.get(c, "") for c in CurvaForm.base_fields}
    inicial.update(cambios)
    return CurvaForm(initial=inicial)


def importar(request, prueba, accion, contexto):
    """Importa los puntos de un archivo (US3) a la tabla de la carga manual. Con un error, la
    tabla queda como estaba; si no se reconocen las columnas, se piden (la tabla leída queda en la
    sesión hasta elegirlas)."""
    previas = filas_enviadas(request.POST)
    tablas = request.session.get(CLAVE_TABLA, {})
    try:
        if accion == "importar":
            archivo = request.FILES.get("archivo")
            if archivo is None:
                raise importacion.ArchivoInvalido("Elegí un archivo .csv o .xlsx.")
            nombre = archivo.name.replace("\\", "/").rsplit("/", 1)[-1][:255]
            tabla = importacion.leer_archivo(archivo)
            columnas = importacion.detectar_columnas(tabla)
            if columnas is None:
                tablas[str(prueba.pk)] = {"nombre": nombre, "filas": tabla}
                request.session[CLAVE_TABLA] = tablas
                return elegir_columnas(request, contexto, tabla, previas)
        else:
            guardada = tablas.get(str(prueba.pk))
            if not guardada:
                raise importacion.ArchivoInvalido("Volvé a importar el archivo.")
            nombre, tabla = guardada["nombre"], guardada["filas"]
            vista = importacion.vista_previa(tabla)
            elegir = ElegirColumnasForm(request.POST, columnas=vista["columnas"])
            if not elegir.is_valid():
                return elegir_columnas(request, contexto, tabla, previas, elegir)
            columnas = elegir.columnas()
        puntos = importacion.extraer_puntos(tabla, columnas)
    except importacion.ArchivoInvalido as exc:
        contexto.update(
            form=form_sin_enviar(request), formset=formset_con(previas), error_archivo=str(exc)
        )
        return render(request, "pruebas/curvas/formulario.html", contexto)
    tablas.pop(str(prueba.pk), None)
    request.session[CLAVE_TABLA] = tablas
    messages.info(
        request, f"Se leyeron {len(puntos)} puntos de {nombre}. Revisalos antes de calcular."
    )
    filas = [(c.replace(".", ","), a.replace(".", ",")) for c, a in puntos]
    contexto.update(
        form=form_sin_enviar(request, archivo_origen=firmar_archivo(nombre)),
        formset=formset_con(filas),
    )
    return render(request, "pruebas/curvas/formulario.html", contexto)


def elegir_columnas(request, contexto, tabla, previas, elegir=None):
    vista = importacion.vista_previa(tabla)
    contexto.update(
        form=form_sin_enviar(request),
        formset=formset_con(previas),
        vista_previa=vista,
        elegir=elegir or ElegirColumnasForm(columnas=vista["columnas"]),
    )
    return render(request, "pruebas/curvas/formulario.html", contexto)


@administracion_requerida
@require_http_methods(["GET", "POST"])
def borrar_curva(request, pk):
    curva = get_object_or_404(CurvaCalibracion.objects.select_related("prueba"), pk=pk)
    prueba = curva.prueba
    if curva.usada:
        messages.error(request, str(curvas.CurvaUsada()))
        return redirect("curvas:detalle", curva.pk)
    if request.method == "GET":
        return render(request, "pruebas/curvas/borrar.html", {"curva": curva, "prueba": prueba})
    if request.POST.get("accion") != "confirmar":
        return redirect("curvas:detalle", curva.pk)
    era_vigente = curva.vigente
    try:
        vigente = curvas.borrar_curva(usuario=request.user, curva_id=curva.pk)
    except curvas.CurvaUsada as exc:
        messages.error(request, str(exc))
        return redirect("curvas:detalle", curva.pk)
    except curvas.CurvaError as exc:
        messages.error(request, str(exc))
        return redirect("curvas:listar", prueba.pk)
    mensaje = "Curva borrada."
    if era_vigente and vigente:
        mensaje += f" Volvió a quedar vigente la del {vigente.fecha_preparacion:%d/%m/%Y}."
    elif era_vigente:
        mensaje += " La prueba quedó sin curva vigente."
    messages.success(request, mensaje)
    return redirect("curvas:listar", prueba.pk)


@administracion_requerida
@require_GET
def plantilla_curva(request):
    respuesta = HttpResponse(importacion.plantilla(), content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = 'attachment; filename="plantilla_curva.csv"'
    return respuesta


def contexto_confirmacion(prueba, borrador):
    datos = borrador["datos"]
    puntos = curvas.leer_puntos(datos["puntos"])
    ajuste = curvas.ajustar(puntos)
    return {
        "prueba": prueba,
        "borrador": borrador,
        "datos": datos,
        "fecha": curvas.leer_fecha(datos["fecha_preparacion"]),
        "cantidad": len(puntos),
        "ajuste": resumen_ajuste(ajuste, prueba.unidad),
        "anterior": prueba.curva_vigente,
        "pendientes": resumen_pendientes(prueba),
        "grafico": datos_grafico(puntos, ajuste, prueba.unidad),
        "url_volver": reverse("catalogo:nueva_curva", args=[prueba.pk])
        + "?solicitud="
        + borrador["clave"],
    }


@administracion_requerida
@require_http_methods(["GET", "POST"])
def confirmar_curva(request, pk):
    prueba = prueba_por_curva(pk)
    if prueba is None:
        return no_es_por_curva(request, pk)
    if request.method == "GET":
        borrador = borrador_de(request, request.GET.get("solicitud"), prueba.pk)
        try:
            if borrador is None:
                raise signing.BadSignature("Sin borrador.")
            tokens.verificar(request, borrador["token"])
            contexto = contexto_confirmacion(prueba, borrador)
        except (signing.BadSignature, curvas.CurvaInvalida):
            return borrador_invalido(request, prueba.pk)
        return render(request, "pruebas/curvas/confirmar.html", contexto)

    try:
        borrador = tokens.verificar(request, request.POST.get("token", ""))
    except signing.BadSignature:
        return borrador_invalido(request, prueba.pk)
    if (borrador["operacion"], borrador["prueba_id"]) != (OPERACION, prueba.pk):
        return borrador_invalido(request, prueba.pk)
    accion = request.POST.get("accion")
    if accion == "cancelar":
        messages.info(request, "No se guardó la curva. Podés seguir editando los puntos.")
        url = reverse("catalogo:nueva_curva", args=[prueba.pk])
        return redirect(f"{url}?solicitud={borrador['clave']}")
    if accion != "confirmar":
        return borrador_invalido(request, prueba.pk)
    try:
        guardado = curvas.guardar_curva(
            usuario=request.user,
            prueba_id=prueba.pk,
            datos=borrador["datos"],
            clave=borrador["clave"],
            calcular_pendientes=request.POST.get("calcular_pendientes") == "1",
        )
    except curvas.CurvaInvalida as exc:
        messages.error(request, str(exc))
        url = reverse("catalogo:nueva_curva", args=[prueba.pk])
        return redirect(f"{url}?solicitud={borrador['clave']}")
    except curvas.CurvaError as exc:
        tokens.descartar(request, borrador["clave"])
        messages.error(request, str(exc))
        return redirect("catalogo:ficha", prueba.pk)
    tokens.descartar(request, borrador["clave"])
    mensaje = f"Curva guardada: es la vigente de {prueba.codigo}."
    if guardado.calculadas:
        resultados = "resultado" if guardado.calculadas == 1 else "resultados"
        mensaje += f" Se calcularon {guardado.calculadas} {resultados}."
    messages.success(request, mensaje)
    return redirect("catalogo:ficha", prueba.pk)


# --- Consulta (cualquier empleado con sesión) -------------------------------------------------


def puede_gestionar(usuario):
    """Si el usuario puede cargar y borrar curvas (el permiso del catálogo, SCRUM-73)."""
    try:
        gestion.autorizar(usuario)
    except gestion.NoAutorizado:
        return False
    return True


@require_GET
def listar(request, pk):
    prueba = get_object_or_404(Prueba, pk=pk)
    lista = list(prueba.curvas.select_related("cargada_por").all())
    return render(
        request,
        "pruebas/curvas/listar.html",
        {
            "prueba": prueba,
            "vigente": next((c for c in lista if c.vigente), None),
            "historicas": [c for c in lista if not c.vigente],
            "puede_gestionar": puede_gestionar(request.user),
            "es_por_curva": prueba.tipo_calculo == TipoCalculo.CURVA,
        },
    )


@require_GET
def detalle(request, pk):
    curva = get_object_or_404(
        CurvaCalibracion.objects.select_related("prueba", "cargada_por"), pk=pk
    )
    puntos = [(p.concentracion, p.absorbancia) for p in curva.puntos.all()]
    ajuste = curvas.Ajuste(
        pendiente=curva.pendiente,
        ordenada=curva.ordenada,
        r2=curva.r2,
        concentracion_min=curva.concentracion_min,
        concentracion_max=curva.concentracion_max,
        absorbancia_min=curva.absorbancia_min,
        absorbancia_max=curva.absorbancia_max,
    )
    return render(
        request,
        "pruebas/curvas/detalle.html",
        {
            "curva": curva,
            "prueba": curva.prueba,
            "puntos": [(numero(c), numero(a)) for c, a in puntos],
            "ajuste": resumen_ajuste(ajuste, curva.prueba.unidad),
            "grafico": datos_grafico(puntos, ajuste, curva.prueba.unidad),
            "puede_borrar": puede_gestionar(request.user) and not curva.usada,
        },
    )
