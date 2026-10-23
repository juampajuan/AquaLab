from django.contrib import messages
from django.core.paginator import Paginator
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CAMPOS_CLIENTE, BuscarClienteForm, EditarClienteForm, RegistroClienteForm
from .models import Cliente, normalizar_numero_documento

CLAVE_SESION = "cliente_pendiente"
CLAVE_ULTIMO_ID = "ultimo_cliente_creado_id"
CLAVE_ULTIMO_EDITADO_ID = "ultimo_cliente_editado_id"
MENSAJE_EXITO = "Cliente registrado correctamente."
MENSAJE_CANCELADO = "Registro de cliente cancelado."
MENSAJE_DUPLICADO = "Ya existe un cliente registrado con este tipo y número de documento."
RESULTADOS_POR_PAGINA = 20
MENSAJE_NO_DISPONIBLE = "El cliente no está disponible."
MENSAJE_ERROR_BD = "No se pudo completar el registro del cliente. Intentá nuevamente."
MENSAJE_EDICION_EXITO = "Datos del cliente actualizados correctamente."
MENSAJE_EDICION_CANCELADA = "Edición de cliente cancelada."
MENSAJE_ERROR_BD_EDICION = "No se pudo actualizar el cliente. Intentá nuevamente."


def clave_sesion_edicion(pk):
    return f"cliente_edicion_{pk}"


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


def actualizar_cliente(cliente, datos):
    """Actualiza el cliente existente. Deja propagar `IntegrityError` (documento ya registrado)."""
    with transaction.atomic():
        for campo in CAMPOS_CLIENTE:
            setattr(cliente, campo, datos[campo])
        cliente.save()
        return cliente


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


def editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    clave_sesion = clave_sesion_edicion(cliente.pk)
    if not cliente.activo:
        request.session.pop(clave_sesion, None)
        messages.warning(request, MENSAJE_NO_DISPONIBLE)
        return redirect("clientes:buscar")

    if request.method == "POST":
        form = EditarClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            request.session[clave_sesion] = form.datos_para_sesion()
            request.session.pop(CLAVE_ULTIMO_EDITADO_ID, None)
            return redirect("clientes:editar_confirmar", pk=cliente.pk)
    else:
        datos = request.session.get(clave_sesion) if request.GET.get("volver") == "1" else None
        if datos is not None:
            form = EditarClienteForm(
                initial={campo: datos.get(campo, "") for campo in CAMPOS_CLIENTE},
                instance=cliente,
            )
        else:
            request.session.pop(clave_sesion, None)
            form = EditarClienteForm(instance=cliente)

    return render(request, "clientes/editar_form.html", {"form": form, "cliente": cliente})


def editar_confirmar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    clave_sesion = clave_sesion_edicion(cliente.pk)
    if not cliente.activo:
        request.session.pop(clave_sesion, None)
        messages.warning(request, MENSAJE_NO_DISPONIBLE)
        return redirect("clientes:buscar")

    datos = request.session.get(clave_sesion)

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "cancelar":
            request.session.pop(clave_sesion, None)
            request.session.pop(CLAVE_ULTIMO_EDITADO_ID, None)
            messages.info(request, MENSAJE_EDICION_CANCELADA)
            return redirect("clientes:detalle", pk=cliente.pk)
        if accion != "confirmar":
            return redirect("clientes:editar_confirmar", pk=cliente.pk)
        if datos is None:
            if request.session.get(CLAVE_ULTIMO_EDITADO_ID) == cliente.pk:
                messages.info(request, MENSAJE_EDICION_EXITO)
                return redirect("clientes:detalle", pk=cliente.pk)
            return redirect("clientes:editar", pk=cliente.pk)
        try:
            actualizar_cliente(cliente, datos)
        except IntegrityError:
            messages.error(request, MENSAJE_DUPLICADO)
            return redirect(f"{reverse('clientes:editar', kwargs={'pk': cliente.pk})}?volver=1")
        except DatabaseError:
            messages.error(request, MENSAJE_ERROR_BD_EDICION)
        else:
            del request.session[clave_sesion]
            request.session[CLAVE_ULTIMO_EDITADO_ID] = cliente.pk
            messages.success(request, MENSAJE_EDICION_EXITO)
            return redirect("clientes:detalle", pk=cliente.pk)
    elif datos is None:
        return redirect("clientes:editar", pk=cliente.pk)

    resumen = {campo: datos.get(campo, "") for campo in CAMPOS_CLIENTE}
    return render(
        request,
        "clientes/editar_confirmar.html",
        {"cliente": cliente, "datos": resumen},
    )


def detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if not cliente.activo:
        messages.warning(request, MENSAJE_NO_DISPONIBLE)
        return redirect("clientes:buscar")
    return render(request, "clientes/detalle.html", {"cliente": cliente})


def buscar_clientes(texto):
    """Clientes activos cuyo nombre, razón social o documento contienen `texto`."""
    filtro = Q(nombre__unaccent__icontains=texto) | Q(razon_social__unaccent__icontains=texto)
    documento = normalizar_numero_documento(texto)
    if documento.isdigit():
        filtro |= Q(numero_documento__contains=documento)
    return Cliente.objects.filter(activo=True).filter(filtro).order_by(*Cliente._meta.ordering)


def buscar(request):
    form = BuscarClienteForm(request.GET) if "q" in request.GET else BuscarClienteForm()
    contexto = {"form": form, "page_obj": None, "q": ""}
    if form.is_bound and form.is_valid():
        texto = form.cleaned_data["q"]
        paginador = Paginator(buscar_clientes(texto), RESULTADOS_POR_PAGINA)
        contexto.update(q=texto, page_obj=paginador.get_page(request.GET.get("page")))
    return render(request, "clientes/buscar.html", contexto)
