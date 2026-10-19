from django.contrib import messages
from django.db import DatabaseError, IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CAMPOS_CLIENTE, RegistroClienteForm
from .models import Cliente

CLAVE_SESION = "cliente_pendiente"
CLAVE_ULTIMO_ID = "ultimo_cliente_creado_id"
MENSAJE_EXITO = "Cliente registrado correctamente."
MENSAJE_CANCELADO = "Registro de cliente cancelado."
MENSAJE_DUPLICADO = "Ya existe un cliente registrado con este tipo y número de documento."
MENSAJE_ERROR_BD = "No se pudo completar el registro del cliente. Intentá nuevamente."


def crear_cliente(datos):
    """Persiste el cliente activo. Deja propagar `IntegrityError` (documento ya registrado)."""
    with transaction.atomic():
        return Cliente.objects.create(
            nombre=datos["nombre"],
            razon_social=datos["razon_social"],
            tipo_documento=datos["tipo_documento"],
            numero_documento=datos["numero_documento"],
            email=datos["email"],
            telefono=datos["telefono"],
            domicilio=datos["domicilio"],
            activo=True,
        )


def registrar(request):
    if request.method == "POST":
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            request.session[CLAVE_SESION] = form.datos_para_sesion()
            request.session.pop(CLAVE_ULTIMO_ID, None)
            return redirect("clientes:registrar_confirmar")
    else:
        datos = request.session.get(CLAVE_SESION)
        if datos:
            form = RegistroClienteForm(
                initial={campo: datos.get(campo, "") for campo in CAMPOS_CLIENTE}
            )
        else:
            form = RegistroClienteForm()
    return render(request, "clientes/registro_form.html", {"form": form})


def registrar_confirmar(request):
    datos = request.session.get(CLAVE_SESION)

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "cancelar":
            request.session.pop(CLAVE_SESION, None)
            request.session.pop(CLAVE_ULTIMO_ID, None)
            messages.info(request, MENSAJE_CANCELADO)
            return redirect("clientes:registrar")
        if accion != "confirmar":
            return redirect("clientes:registrar_confirmar")
        if datos is None:
            ultimo_id = request.session.get(CLAVE_ULTIMO_ID)
            if ultimo_id and Cliente.objects.filter(pk=ultimo_id).exists():
                messages.info(request, MENSAJE_EXITO)
                return redirect("clientes:detalle", pk=ultimo_id)
            return redirect("clientes:registrar")
        try:
            cliente = crear_cliente(datos)
        except IntegrityError:
            messages.error(request, MENSAJE_DUPLICADO)
            return redirect("clientes:registrar")
        except DatabaseError:
            messages.error(request, MENSAJE_ERROR_BD)
        else:
            del request.session[CLAVE_SESION]
            request.session[CLAVE_ULTIMO_ID] = cliente.pk
            messages.success(request, MENSAJE_EXITO)
            return redirect("clientes:detalle", pk=cliente.pk)
    elif datos is None:
        return redirect("clientes:registrar")

    resumen = {campo: datos.get(campo, "") for campo in CAMPOS_CLIENTE}
    return render(request, "clientes/registro_confirmar.html", {"datos": resumen})


def detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, "clientes/detalle.html", {"cliente": cliente})
