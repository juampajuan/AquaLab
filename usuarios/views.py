from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db import DatabaseError, IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.views.decorators.http import require_GET

from .context_processors import huella_para
from .forms import FormularioInicioSesion, RegistroForm
from .models import Usuario

CLAVE_SESION = "registro_pendiente"
MENSAJE_RECIBIDO = (
    "Registro recibido. Vas a poder ingresar cuando un administrador apruebe tu cuenta."
)


def crear_usuario_pendiente(datos):
    """Crea la cuenta pendiente de aprobación. Deja propagar `IntegrityError` (correo tomado)."""
    with transaction.atomic():
        return Usuario.objects.create(
            first_name=datos["first_name"],
            last_name=datos["last_name"],
            email=datos["email"],
            # Ya viene hasheada desde `RegistroForm.datos_para_sesion` (no usar `create_user`).
            password=datos["password"],
            is_active=False,
        )


@login_not_required
def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            request.session[CLAVE_SESION] = form.datos_para_sesion()
            return redirect("usuarios:registro_confirmar")
    else:
        datos = request.session.get(CLAVE_SESION, {})
        form = RegistroForm(
            initial={campo: datos.get(campo) for campo in ("first_name", "last_name", "email")}
        )
    return render(request, "usuarios/registro_form.html", {"form": form})


@login_not_required
def registro_confirmar(request):
    datos = request.session.get(CLAVE_SESION)

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "cancelar":
            request.session.pop(CLAVE_SESION, None)
            messages.info(request, "Registro cancelado.")
            return redirect("usuarios:registro")
        if accion != "confirmar":
            return redirect("usuarios:registro_confirmar")
        if datos is None:
            # Confirmación repetida: la cuenta ya se creó en el POST anterior.
            messages.info(request, MENSAJE_RECIBIDO)
            return redirect("usuarios:registro_recibido")
        try:
            crear_usuario_pendiente(datos)
        except IntegrityError:
            messages.error(request, "Este correo no está disponible.")
            return redirect("usuarios:registro")
        except DatabaseError:
            messages.error(request, "No se pudo completar el registro. Intentá nuevamente.")
        else:
            del request.session[CLAVE_SESION]
            messages.success(request, MENSAJE_RECIBIDO)
            return redirect("usuarios:registro_recibido")
    elif datos is None:
        return redirect("usuarios:registro")

    resumen = {campo: datos[campo] for campo in ("first_name", "last_name", "email")}
    return render(request, "usuarios/registro_confirmar.html", {"datos": resumen})


@login_not_required
def registro_recibido(request):
    return render(request, "usuarios/registro_recibido.html")


class InicioSesionView(LoginView):
    authentication_form = FormularioInicioSesion
    template_name = "usuarios/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse("inicio")


class CerrarSesionView(LogoutView):
    def get_success_url(self):
        return reverse("usuarios:login")


@require_GET
def sesion(request):
    original = request.headers.get("X-AquaLab-Sesion", "")
    actual = huella_para(request)
    valida = bool(original and actual and constant_time_compare(original, actual))
    return HttpResponse(status=204 if valida else 409)
