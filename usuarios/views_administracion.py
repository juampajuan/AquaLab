from urllib.parse import urlencode

from django.contrib import messages
from django.core import signing
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Exists, OuterRef, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from pruebas.models import Prueba

from . import confirmaciones_administracion as confirmaciones
from .forms_administracion import OperacionForm, RolForm
from .models import Usuario
from .permisos_administracion import GRUPO_ADMINISTRADORES, administracion_requerida
from .servicios_administracion import GestionUsuarioError, comprobar_revision, instantanea

BASE = "usuarios/administracion/"


@administracion_requerida
@require_http_methods(["GET"])
def solicitudes(request):
    pagina = Paginator(
        Usuario.objects.filter(aprobada=False, is_active=False).order_by("-date_joined", "-pk"), 20
    ).get_page(request.GET.get("page"))
    return render(request, BASE + "solicitudes.html", {"page_obj": pagina})


def _mostrar_confirmacion(request, usuario, operacion, titulo, borrador):
    datos = borrador["datos"]
    return render(
        request,
        BASE + "confirmar.html",
        {
            "usuario": usuario,
            "titulo": titulo,
            "operacion": operacion,
            "token": borrador["token"],
            "consecuencia": "La cuenta quedará Activa sin reenviar el aviso inicial."
            if datos.get("activa")
            else "La cuenta quedará Desactivada y perderá el acceso.",
            "rol_anterior": "Bioquímico"
            if usuario.groups.filter(name="Bioquímicos").exists()
            else "Usuario común",
            "rol_propuesto": "Bioquímico" if datos.get("bioquimico") else "Usuario común",
        },
    )


def _operar(request, pk, operacion, titulo, destino="solicitudes", datos=None):
    url = "administracion:" + destino
    datos = datos or {}
    if request.method == "GET":
        usuario = get_object_or_404(Usuario, pk=pk)
        if operacion in {"aprobar", "rechazar"} and usuario.aprobada:
            messages.warning(request, "La cuenta ya no está pendiente.")
            return redirect(url)
        if operacion in {"estado", "rol"}:
            if not usuario.aprobada:
                messages.warning(request, "Gestioná esta cuenta desde Solicitudes de cuenta.")
                return redirect(url)
            if operacion == "estado" and not datos["activa"] and usuario.pk == request.user.pk:
                messages.warning(request, "No podés desactivar tu propia cuenta.")
                return redirect(url)
        try:
            borrador = confirmaciones.preparar(
                request, operacion, pk, usuario.version_administrativa, datos, instantanea(usuario)
            )
        except (signing.BadSignature, GestionUsuarioError) as exc:
            messages.warning(request, str(exc))
            return redirect(url)
        return _mostrar_confirmacion(request, usuario, operacion, titulo, borrador)
    form = OperacionForm(request.POST)
    if not form.is_valid():
        return render(
            request, BASE + "confirmar.html", {"titulo": titulo, "form": form}, status=200
        )
    try:
        borrador = confirmaciones.verificar(request, form.cleaned_data["token"])
        if borrador["usuario_id"] != pk or borrador["operacion"] != operacion:
            raise signing.BadSignature("La operación no coincide.")
        if operacion == "estado" and borrador["datos"] != datos:
            raise signing.BadSignature("La acción no coincide.")
        confirmaciones.confirmar(
            request, form.cleaned_data["token"], cancelar=form.cleaned_data["accion"] == "cancelar"
        )
    except signing.BadSignature:
        messages.warning(
            request,
            "La confirmación es inválida, venció o ya se utilizó. Iniciá una nueva revisión.",
        )
    except GestionUsuarioError as exc:
        messages.warning(request, str(exc))
    except DatabaseError:
        messages.error(request, "No se pudo guardar la operación. Intentá nuevamente.")
    else:
        messages.success(
            request,
            "Operación cancelada."
            if form.cleaned_data["accion"] == "cancelar"
            else "Operación completada.",
        )
    return redirect(url)


@administracion_requerida
@require_http_methods(["GET", "POST"])
def aprobar(request, pk):
    return _operar(request, pk, "aprobar", "Aprobar solicitud")


@administracion_requerida
@require_http_methods(["GET", "POST"])
def rechazar(request, pk):
    return _operar(request, pk, "rechazar", "Rechazar solicitud")


def _contexto_rol(request, usuario):
    return confirmaciones.firmar_ficha(request, instantanea(usuario), operacion="rol-panel")


@administracion_requerida
@require_http_methods(["GET"])
def usuarios(request):
    pertenencia = Usuario.groups.through.objects.filter(
        usuario_id=OuterRef("pk"), group__name="Bioquímicos"
    )
    administradores = Usuario.groups.through.objects.filter(
        usuario_id=OuterRef("pk"), group__name=GRUPO_ADMINISTRADORES
    )
    consulta = Usuario.objects.annotate(
        es_bioquimico=Exists(pertenencia), es_administrador=Exists(administradores)
    ).order_by("last_name", "first_name", "email", "pk")
    pagina = Paginator(consulta, 20).get_page(request.GET.get("page"))
    return render(request, BASE + "usuarios.html", {"page_obj": pagina})


@administracion_requerida
@require_http_methods(["GET", "POST"])
def cambiar_rol(request, pk):
    if request.method == "POST" and request.POST.get("accion") != "revisar":
        return _operar(request, pk, "rol", "Confirmar rol profesional", "usuarios")
    usuario = get_object_or_404(Usuario, pk=pk)
    if not usuario.aprobada:
        messages.warning(request, "Gestioná esta cuenta desde Solicitudes de cuenta.")
        return redirect("administracion:usuarios")
    rol_actual = "bioquimico" if usuario.groups.filter(name="Bioquímicos").exists() else "comun"
    if request.method == "POST":
        try:
            original = confirmaciones.leer_ficha(
                request, request.POST.get("contexto", ""), operacion="rol-panel"
            )
            if original["pk"] != pk:
                raise signing.BadSignature("La cuenta no coincide.")
            comprobar_revision(usuario, original["version"], original)
        except (signing.BadSignature, KeyError):
            messages.warning(
                request, "La confirmación del rol es inválida o venció. Revisá nuevamente."
            )
            return redirect("administracion:usuarios")
        except GestionUsuarioError as exc:
            messages.warning(request, str(exc))
            return redirect("administracion:usuarios")
    form = RolForm(
        request.POST if request.method == "POST" else None,
        rol_actual=rol_actual,
        initial={
            "contexto": _contexto_rol(request, usuario),
            "accion": "revisar",
            "rol": "comun" if rol_actual == "bioquimico" else "bioquimico",
        },
    )
    if request.method == "POST" and form.is_valid():
        try:
            borrador = confirmaciones.preparar(
                request,
                "rol",
                pk,
                original["version"],
                {"bioquimico": form.cleaned_data["rol"] == "bioquimico"},
                original,
            )
        except (signing.BadSignature, KeyError):
            messages.warning(
                request, "La confirmación del rol es inválida o venció. Revisá nuevamente."
            )
            return redirect("administracion:usuarios")
        except GestionUsuarioError as exc:
            messages.warning(request, str(exc))
            return redirect("administracion:usuarios")
        return _mostrar_confirmacion(request, usuario, "rol", "Confirmar rol profesional", borrador)
    return render(
        request,
        BASE + "rol.html",
        {
            "usuario": usuario,
            "form": form,
            "rol_actual": "Bioquímico" if rol_actual == "bioquimico" else "Usuario común",
        },
    )


@administracion_requerida
@require_http_methods(["GET", "POST"])
def desactivar(request, pk):
    return _operar(request, pk, "estado", "Desactivar cuenta", "usuarios", {"activa": False})


@administracion_requerida
@require_http_methods(["GET", "POST"])
def reactivar(request, pk):
    return _operar(request, pk, "estado", "Reactivar cuenta", "usuarios", {"activa": True})


@administracion_requerida
@require_http_methods(["GET"])
def pruebas(request):
    busqueda = request.GET.get("q", "").strip()
    consulta = Prueba.objects.filter(
        Q(codigo__icontains=busqueda) | Q(nombre__icontains=busqueda)
    ).order_by("codigo", "pk")
    pagina = Paginator(consulta, 20).get_page(request.GET.get("page"))
    # Activas que usan en su fórmula alguna inactiva: se marcan para reemplazarla (SCRUM-73).
    from pruebas.gestion import dependencias_inactivas

    dependencias = dependencias_inactivas()
    for prueba in pagina:
        prueba.usa_inactivas = dependencias.get(prueba.pk, [])
    return render(
        request,
        BASE + "pruebas.html",
        {"page_obj": pagina, "q": busqueda, "parametros": urlencode({"q": busqueda})},
    )
