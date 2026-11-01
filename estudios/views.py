from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core import signing
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import format_html

from clientes.models import normalizar_numero_documento
from muestras.models import Muestra
from pruebas.limites import Evaluacion, LimitesAplicables, evaluar, limites_aplicables

from . import calculo, servicios
from .catalogo import CatalogoNoDisponible
from .confirmaciones import cargar_token, descartar, pendientes, preparar
from .forms import (
    AgregarPruebaForm,
    BuscarEstudioForm,
    CargarMedicionesForm,
    CorregirMedicionesForm,
    CrearEstudioForm,
    ValidarResultadosForm,
)
from .models import EstadoPruebaEstudio, Estudio, OrigenLimites, Validacion
from .servicios import (
    CargarMedicionesError,
    CorregirMedicionesError,
    CrearEstudioError,
    GestionPruebasError,
    PruebaYaAsignada,
    PruebaYaQuitada,
    ValidarResultadosError,
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
        estudio.pruebas_asignadas.select_related(
            "prueba", "medicion", "medicion__cargada_por", "medicion__corregida_por", "resultado"
        )
        .prefetch_related("prueba__limites_vertido", validaciones_vigentes())
        .order_by("prueba__codigo", "pk")
    )
    todas = {a.prueba.codigo: a for a in pruebas_asignadas}
    for asignacion in pruebas_asignadas:
        asignacion.motivo_sin_resultado = calculo.motivo_sin_resultado(asignacion, todas)
    evaluar_asignaciones(estudio, pruebas_asignadas)
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
            "hay_mediciones": any(calculo.tiene_medicion(a) for a in pruebas_asignadas),
            "pruebas_para_medir": sum(
                1
                for a in pruebas_asignadas
                if a.estado == EstadoPruebaEstudio.PENDIENTE and not a.prueba.es_calculada
            ),
            "hay_para_validar": any(validable(a) for a in pruebas_asignadas),
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


def asignaciones_para_medir(estudio):
    return (
        estudio.pruebas_asignadas.filter(
            estado=EstadoPruebaEstudio.PENDIENTE, prueba__es_calculada=False
        )
        .select_related("prueba")
        .order_by("prueba__codigo", "pk")
    )


def mensaje_guardadas(estudio, guardadas):
    codigos = ", ".join(m.asignacion.prueba.codigo for m in guardadas)
    if len(guardadas) == 1:
        return f"Se guardó 1 medición del estudio {estudio.pk}: {codigos}."
    return f"Se guardaron {len(guardadas)} mediciones del estudio {estudio.pk}: {codigos}."


def cargar_mediciones(request, pk):
    estudio = get_object_or_404(Estudio.objects.select_related("muestra"), pk=pk)
    accion = request.POST.get("accion") if request.method == "POST" else None
    if accion != "confirmar" and not estudio.admite_mediciones:
        # Al confirmar, la regla la revalida el servicio con el estudio bloqueado.
        messages.error(request, "Este estudio ya no admite carga de mediciones.")
        return redirect("estudios:detalle", pk=estudio.pk)
    if request.method == "POST" and accion not in ("revisar", "editar", "confirmar"):
        messages.error(request, "La acción no es válida.")
        return redirect("estudios:detalle", pk=estudio.pk)
    if accion == "confirmar":
        # Con todas las no calculadas, el valor de una prueba que mientras tanto quedó
        # Cargada llega al servicio, que la omite.
        asignaciones = estudio.pruebas_asignadas.filter(prueba__es_calculada=False)
        asignaciones = asignaciones.select_related("prueba").order_by("prueba__codigo", "pk")
    else:
        asignaciones = asignaciones_para_medir(estudio)
    form = CargarMedicionesForm(request.POST or None, asignaciones=asignaciones)
    calculadas = estudio.pruebas_asignadas.filter(
        estado=EstadoPruebaEstudio.PENDIENTE, prueba__es_calculada=True
    ).select_related("prueba")
    contexto = {
        "estudio": estudio,
        "form": form,
        "calculadas": calculadas.order_by("prueba__codigo"),
    }
    if accion in (None, "editar") or not form.is_valid():
        return render(request, "estudios/cargar_mediciones.html", contexto)
    if accion == "revisar":
        return render(request, "estudios/cargar_mediciones_confirmar.html", contexto)
    try:
        resultado = servicios.cargar_mediciones(estudio.pk, form.valores(), request.user)
    except CargarMedicionesError as exc:
        messages.error(request, str(exc))
    except DatabaseError:
        messages.error(request, "No se pudieron guardar las mediciones. Intentá nuevamente.")
    else:
        if resultado.guardadas:
            messages.success(request, mensaje_guardadas(estudio, resultado.guardadas))
        for prueba, motivo in resultado.omitidas:
            messages.warning(request, f"{prueba.codigo}: {motivo}.")
        for prueba, motivo in resultado.sin_calcular:
            messages.warning(
                request, f"{prueba.codigo}: no se pudo calcular el resultado ({motivo})."
            )
        if quitadas := form.pruebas_quitadas():
            messages.warning(
                request,
                f"{quitadas} prueba(s) ya no forman parte del estudio; su medición no se guardó.",
            )
    return redirect("estudios:detalle", pk=estudio.pk)


INFORME_EMITIDO = (
    "El estudio ya tiene el informe emitido: sus mediciones y resultados no se pueden cambiar."
)


def mensaje_corregidas(estudio, corregidas):
    codigos = ", ".join(m.asignacion.prueba.codigo for m in corregidas)
    if len(corregidas) == 1:
        return f"Se corrigió 1 medición del estudio {estudio.pk}: {codigos}."
    return f"Se corrigieron {len(corregidas)} mediciones del estudio {estudio.pk}: {codigos}."


def mensaje_borradas(estudio, borradas):
    codigos = ", ".join(p.codigo for p in borradas)
    if len(borradas) == 1:
        return f"Se borró 1 medición del estudio {estudio.pk}: {codigos}."
    return f"Se borraron {len(borradas)} mediciones del estudio {estudio.pk}: {codigos}."


def corregir_mediciones(request, pk):
    estudio = get_object_or_404(Estudio.objects.select_related("muestra"), pk=pk)
    accion = request.POST.get("accion") if request.method == "POST" else None
    if accion != "confirmar" and not estudio.admite_correcciones:
        # Al confirmar, la regla la revalida el servicio con el estudio bloqueado.
        messages.error(request, INFORME_EMITIDO)
        return redirect("estudios:detalle", pk=estudio.pk)
    if request.method == "POST" and accion not in ("revisar", "editar", "confirmar"):
        messages.error(request, "La acción no es válida.")
        return redirect("estudios:detalle", pk=estudio.pk)
    asignaciones = estudio.pruebas_asignadas.select_related(
        "prueba", "medicion", "medicion__cargada_por", "medicion__corregida_por"
    ).order_by("prueba__codigo", "pk")
    if accion == "confirmar":
        # También las que ya no tienen medición, para que un reenvío de un borrado se informe
        # («ya no tenía medición») en lugar de «No hay cambios para guardar».
        enviadas = [n.removeprefix("original_") for n in request.POST if n.startswith("original_")]
        asignaciones = asignaciones.filter(pk__in=[pk for pk in enviadas if pk.isdigit()])
    else:
        asignaciones = asignaciones.filter(medicion__isnull=False)
    form = CorregirMedicionesForm(request.POST or None, asignaciones=asignaciones)
    contexto = {"estudio": estudio, "form": form}
    if accion in (None, "editar") or not form.is_valid():
        return render(request, "estudios/corregir_mediciones.html", contexto)
    if accion == "revisar":
        todas = calculo.por_codigo(estudio)
        cambios = form.cambios()
        contexto["hay_borrados"] = any(nuevo is None for _, _, nuevo in cambios)
        codigos = calculo.afectadas(todas, {a.prueba.codigo for a, _, _ in cambios})
        contexto["pierden_validacion"] = [
            todas[c] for c in sorted(codigos) if todas[c].estado == EstadoPruebaEstudio.COMPLETADA
        ]
        return render(request, "estudios/corregir_mediciones_confirmar.html", contexto)
    cambios = {a.pk: (anterior, nuevo) for a, anterior, nuevo in form.cambios()}
    try:
        resultado = servicios.corregir_mediciones(estudio.pk, cambios, request.user)
    except CorregirMedicionesError as exc:
        messages.error(request, str(exc))
    except DatabaseError:
        messages.error(request, "No se pudieron guardar las correcciones. Intentá nuevamente.")
    else:
        if resultado.corregidas:
            messages.success(request, mensaje_corregidas(estudio, resultado.corregidas))
        if resultado.borradas:
            messages.success(request, mensaje_borradas(estudio, resultado.borradas))
        for prueba, motivo in resultado.omitidas:
            messages.warning(request, f"{prueba.codigo}: {motivo}.")
        for prueba, motivo in resultado.sin_calcular:
            messages.warning(
                request, f"{prueba.codigo}: no se pudo calcular el resultado ({motivo})."
            )
    return redirect("estudios:detalle", pk=estudio.pk)


INFORME_EMITIDO_VALIDAR = (
    "El estudio ya tiene el informe emitido: sus resultados no se pueden validar."
)
TIPOS_EVALUACION = {
    Evaluacion.CUMPLE: "success",
    Evaluacion.FUERA_DE_NORMA: "danger",
    Evaluacion.SIN_LIMITE: "neutral",
}


def validaciones_vigentes():
    return Prefetch(
        "validaciones",
        queryset=Validacion.objects.filter(anulada=False).select_related("validada_por"),
        to_attr="validaciones_vigentes",
    )


def validable(asignacion):
    return asignacion.estado == EstadoPruebaEstudio.CARGADA and calculo.tiene_resultado(asignacion)


def texto_limite(limites):
    minimo, maximo = limites.minimo.strip(), limites.maximo.strip()
    if minimo and maximo:
        return f"{minimo} a {maximo}"
    if maximo:
        return f"máx. {maximo}"
    if minimo:
        return f"mín. {minimo}"
    return ""


def evaluar_asignaciones(estudio, asignaciones):
    """Adjunta a cada asignación con resultado su evaluación (US 6.4): la guardada al validar si
    está Completada (FR-012); si no, la de los límites vigentes del catálogo (FR-008).

    Espera `prueba__limites_vertido` y `validaciones_vigentes()` precargados.
    """
    for asignacion in asignaciones:
        vigentes = getattr(asignacion, "validaciones_vigentes", [])
        asignacion.validacion = vigentes[0] if vigentes else None
        asignacion.evaluacion = None
        if not calculo.tiene_resultado(asignacion):
            continue
        if asignacion.validacion and asignacion.estado == EstadoPruebaEstudio.COMPLETADA:
            v = asignacion.validacion
            limites = LimitesAplicables(v.limite_min, v.limite_max, v.norma, v.origen_limites)
            evaluacion = Evaluacion(v.evaluacion)
        else:
            limites = limites_aplicables(asignacion.prueba, estudio.muestra.tipo_vertido)
            evaluacion = evaluar(asignacion.resultado.valor, limites)
        asignacion.evaluacion = evaluacion
        asignacion.evaluacion_tipo = TIPOS_EVALUACION[evaluacion]
        asignacion.limite_texto = texto_limite(limites)
        asignacion.limite_norma = limites.norma
        asignacion.limite_origen = (
            "" if limites.origen == OrigenLimites.GENERAL else OrigenLimites(limites.origen).label
        )


def mensaje_validadas(estudio, validadas):
    codigos = ", ".join(p.codigo for p in validadas)
    if len(validadas) == 1:
        return f"Se validó 1 resultado del estudio {estudio.pk}: {codigos}."
    return f"Se validaron {len(validadas)} resultados del estudio {estudio.pk}: {codigos}."


@permission_required("estudios.validar_resultados", raise_exception=True)
def validar_resultados(request, pk):
    estudio = get_object_or_404(Estudio.objects.select_related("muestra"), pk=pk)
    accion = request.POST.get("accion") if request.method == "POST" else None
    if accion != "confirmar" and not estudio.admite_correcciones:
        # Al confirmar, la regla la revalida el servicio con el estudio bloqueado.
        messages.error(request, INFORME_EMITIDO_VALIDAR)
        return redirect("estudios:detalle", pk=estudio.pk)
    if request.method == "POST" and accion not in (
        "revisar",
        "editar",
        "marcar_todas",
        "confirmar",
    ):
        messages.error(request, "La acción no es válida.")
        return redirect("estudios:detalle", pk=estudio.pk)
    asignaciones = (
        estudio.pruebas_asignadas.select_related("prueba", "resultado")
        .prefetch_related("prueba__limites_vertido", validaciones_vigentes())
        .order_by("prueba__codigo", "pk")
    )
    if accion == "confirmar":
        # Las enviadas, aunque ya estén validadas: así un reenvío se informa en vez de fallar.
        enviadas = [
            n.removeprefix("resultado_") for n in request.POST if n.startswith("resultado_")
        ]
        asignaciones = asignaciones.filter(pk__in=[pk for pk in enviadas if pk.isdigit()])
    else:
        asignaciones = asignaciones.filter(
            estado=EstadoPruebaEstudio.CARGADA, resultado__isnull=False
        )
    filas = list(asignaciones)
    evaluar_asignaciones(estudio, filas)
    if accion == "marcar_todas":
        form = ValidarResultadosForm(filas=filas, marcar_todas=True)
    else:
        form = ValidarResultadosForm(request.POST or None, filas=filas)
    contexto = {"estudio": estudio, "form": form}
    if accion in (None, "editar", "marcar_todas") or not form.is_valid():
        return render(request, "estudios/validar_resultados.html", contexto)
    if accion == "revisar":
        elegidas = form.resumen()
        sin_validar = estudio.pruebas_asignadas.exclude(estado=EstadoPruebaEstudio.COMPLETADA)
        contexto["elegidas"] = elegidas
        contexto["no_cumplen"] = [a for a in elegidas if a.evaluacion == Evaluacion.FUERA_DE_NORMA]
        contexto["finalizara"] = sin_validar.count() == len(elegidas)
        return render(request, "estudios/validar_resultados_confirmar.html", contexto)
    try:
        resultado = servicios.validar_resultados(estudio.pk, form.elegidas(), request.user)
    except ValidarResultadosError as exc:
        messages.error(request, str(exc))
    except DatabaseError:
        messages.error(request, "No se pudieron validar los resultados. Intentá nuevamente.")
    else:
        if resultado.validadas:
            messages.success(request, mensaje_validadas(estudio, resultado.validadas))
        if resultado.finalizado:
            messages.success(request, f"El estudio {estudio.pk} quedó Finalizado.")
        for prueba, motivo in resultado.omitidas:
            messages.warning(request, f"{prueba.codigo}: {motivo}.")
    return redirect("estudios:detalle", pk=estudio.pk)
