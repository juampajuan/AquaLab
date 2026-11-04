"""Políticas de autorización; no conceden permisos ni sustituyen el backend Django."""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Usuario

GRUPO_ADMINISTRADORES = "Administradores"
PERMISO_ADMINISTRACION = "usuarios.administrar_panel"


def administracion_requerida(vista):
    @login_required
    @wraps(vista)
    def protegida(request, *args, **kwargs):
        autorizar_administracion(request.user)
        return vista(request, *args, **kwargs)

    return protegida


def _usuario_activo(usuario):
    if usuario is None or not usuario.is_authenticated or usuario.pk is None:
        return None
    # Una instancia nueva evita atributos de estado y cachés de permisos obsoletos.
    return Usuario.objects.filter(pk=usuario.pk, is_active=True).first()


def _cumple_politica_panel(usuario):
    if usuario is None or not usuario.groups.filter(name=GRUPO_ADMINISTRADORES).exists():
        return False
    permiso = {
        "content_type__app_label": "usuarios",
        "content_type__model": "usuario",
        "codename": "administrar_panel",
    }
    if usuario.user_permissions.filter(**permiso).exists():
        return True
    return usuario.groups.filter(
        **{f"permissions__{campo}": valor for campo, valor in permiso.items()}
    ).exists()


def tiene_acceso_administracion(usuario):
    """Exige grupo y asignación real, incluso para superusuarios."""
    return _cumple_politica_panel(_usuario_activo(usuario))


def autorizar_administracion(usuario):
    """Devuelve el actor vigente o deniega el acceso al nuevo panel."""
    vigente = _usuario_activo(usuario)
    if not _cumple_politica_panel(vigente):
        raise PermissionDenied(
            "Se requiere pertenecer a Administradores y el permiso administrativo."
        )
    return vigente


def autorizar_admin_django(usuario, accion):
    """Conserva la política del admin para sus futuros adaptadores de change/delete."""
    if accion not in {"change", "delete"}:
        raise ValueError("La acción administrativa no es válida.")
    vigente = _usuario_activo(usuario)
    if (
        vigente is None
        or not vigente.is_staff
        or not vigente.has_perm(f"usuarios.{accion}_usuario")
    ):
        raise PermissionDenied("No tenés permiso para realizar esta acción en Django Admin.")
    return vigente
