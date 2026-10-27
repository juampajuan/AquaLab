import datetime

from django.contrib import messages
from django.db import DatabaseError
from django.shortcuts import redirect, render
from django.urls import reverse

from clientes.models import Cliente

from .forms import CAMPOS_MUESTRA, RegistroMuestraForm, datos_clientes
from .models import Origen, TipoVertido
from .servicios import (
    MENSAJE_CLIENTE_NO_DISPONIBLE,
    MuestraNoDisponible,
    nombre_por_defecto,
    registrar_muestra,
)

CLAVE_SESION = "muestra_pendiente"
CLAVE_ULTIMO_PI = "ultima_muestra_pi"
MENSAJE_EXITO = "Muestra registrada con N° PI {numero_pi}."
MENSAJE_CANCELADO = "Registro de muestra cancelado."
MENSAJE_ERROR_BD = "No se pudo registrar la muestra. Intentá nuevamente."


def url_volver():
    return f"{reverse('muestras:registrar')}?volver=1"


def armar_resumen(datos):
    """Datos del borrador listos para mostrar, o `None` si el cliente ya no existe."""
    cliente = Cliente.objects.filter(pk=datos["cliente"]).first()
    if cliente is None:
        return None
    origen = Origen.objects.filter(pk=datos["origen"]).first() if datos["origen"] else None
    return {
        "cliente": cliente,
        "origen": origen.nombre if origen else datos["origen_nuevo"],
        "origen_es_nuevo": origen is None,
        "fecha_muestreo": datetime.date.fromisoformat(datos["fecha_muestreo"]),
        "fecha_ingreso": datetime.date.fromisoformat(datos["fecha_ingreso"]),
        "sitio_extraccion": datos["sitio_extraccion"],
        "tipo_vertido": TipoVertido(datos["tipo_vertido"]).label,
        "nombre": datos["nombre"] or nombre_por_defecto(cliente),
        "nombre_es_por_defecto": not datos["nombre"],
        "responsable_muestreo": datos["responsable_muestreo"],
    }


def registrar(request):
    if request.method == "POST":
        form = RegistroMuestraForm(request.POST)
        if form.is_valid():
            request.session[CLAVE_SESION] = form.datos_para_sesion()
            request.session.pop(CLAVE_ULTIMO_PI, None)
            return redirect("muestras:registrar_confirmar")
    else:
        datos = request.session.get(CLAVE_SESION) if request.GET.get("volver") == "1" else None
        if datos is not None:
            form = RegistroMuestraForm(
                initial={campo: datos.get(campo, "") for campo in CAMPOS_MUESTRA}
            )
        else:
            request.session.pop(CLAVE_SESION, None)
            form = RegistroMuestraForm()
    return render(
        request,
        "muestras/registro_form.html",
        {
            "form": form,
            "cliente_elegido": form.cliente_elegido,
            "clientes_datos": datos_clientes(),
        },
    )


def registrar_confirmar(request):
    datos = request.session.get(CLAVE_SESION)

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "cancelar":
            request.session.pop(CLAVE_SESION, None)
            messages.info(request, MENSAJE_CANCELADO)
            return redirect("muestras:registrar")
        if accion != "confirmar":
            return redirect("muestras:registrar_confirmar")
        if datos is None:
            ultimo_pi = request.session.get(CLAVE_ULTIMO_PI)
            if ultimo_pi:
                messages.info(request, MENSAJE_EXITO.format(numero_pi=ultimo_pi))
            return redirect("muestras:registrar")
        try:
            muestra = registrar_muestra(datos, request.user)
        except MuestraNoDisponible as exc:
            messages.warning(request, exc.mensaje)
            return redirect(url_volver())
        except DatabaseError:
            messages.error(request, MENSAJE_ERROR_BD)
        else:
            del request.session[CLAVE_SESION]
            request.session[CLAVE_ULTIMO_PI] = muestra.numero_pi
            messages.success(request, MENSAJE_EXITO.format(numero_pi=muestra.numero_pi))
            return redirect("muestras:registrar")
    elif datos is None:
        return redirect("muestras:registrar")

    resumen = armar_resumen(datos)
    if resumen is None:
        messages.warning(request, MENSAJE_CLIENTE_NO_DISPONIBLE)
        return redirect(url_volver())
    return render(request, "muestras/registro_confirmar.html", {"datos": resumen})
