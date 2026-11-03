"""Transiciones coordinadas para el panel y el admin de Django."""

from contextlib import contextmanager
from functools import partial

from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models.deletion import ProtectedError

from . import notificaciones
from .models import Usuario
from .permisos_administracion import autorizar_admin_django, autorizar_administracion


class GestionUsuarioError(Exception):
    """Conflicto de revisión o transición que debe informarse al operador."""


def instantanea(usuario):
    return {
        "pk": usuario.pk,
        "email": usuario.email,
        "first_name": usuario.first_name,
        "last_name": usuario.last_name,
        "aprobada": usuario.aprobada,
        "is_active": usuario.is_active,
        "is_staff": usuario.is_staff,
        "is_superuser": usuario.is_superuser,
        "version": usuario.version_administrativa,
        "grupos": sorted(grupo.pk for grupo in usuario.groups.all()),
        "permisos": sorted(permiso.pk for permiso in usuario.user_permissions.all()),
    }


@contextmanager
def bloquear(request, objetivos, *, canal="panel", accion="change"):
    """Autorización antes de leer objetivos y nuevamente bajo bloqueo ordenado."""

    def autorizar():
        if canal == "panel":
            return autorizar_administracion(request.user)
        return autorizar_admin_django(request.user, accion)

    actor = autorizar()
    with transaction.atomic():
        filas = {
            u.pk: u
            for u in Usuario.objects.select_for_update()
            .filter(pk__in={actor.pk, *objetivos})
            .order_by("pk")
        }
        autorizar()
        yield filas


def comprobar_revision(usuario, version, original=None):
    if usuario.version_administrativa != version or (
        original is not None and instantanea(usuario) != original
    ):
        raise GestionUsuarioError("La cuenta cambió. Revisá nuevamente la operación.")


def _preparar_estado(request, usuario, activa):
    if request.user.pk == usuario.pk and not activa:
        raise GestionUsuarioError("No podés desactivar tu propia cuenta.")
    pendiente = not usuario.aprobada
    usuario.is_active = activa
    usuario.aprobada = usuario.aprobada or activa
    return pendiente and activa


def _avisar_aprobacion(request, usuario):
    transaction.on_commit(partial(notificaciones.avisar_aprobacion, request, usuario))


def _estado(request, usuario, activa):
    if request.user.pk == usuario.pk and not activa:
        raise GestionUsuarioError("No podés desactivar tu propia cuenta.")
    if usuario.is_active == activa:
        return False
    aprobar = _preparar_estado(request, usuario, activa)
    usuario.version_administrativa += 1
    usuario.save(update_fields=["is_active", "aprobada", "version_administrativa"])
    if aprobar:
        _avisar_aprobacion(request, usuario)
    return True


def _resolver(request, usuario, operacion, registrar=None):
    if operacion not in {"aprobar", "rechazar"}:
        raise GestionUsuarioError("Operación inválida.")
    if usuario.aprobada or usuario.is_active:
        return False
    if operacion == "aprobar":
        return _estado(request, usuario, True)
    from informes.models import FirmaProfesional

    if FirmaProfesional.objects.filter(usuario_id=usuario.pk).exists():
        raise GestionUsuarioError("No se puede rechazar: la cuenta conserva firma profesional.")
    nombre, email = usuario.first_name, usuario.email
    try:
        # Savepoint para mantener utilizable la transacción del lote ante PROTECT.
        with transaction.atomic():
            if registrar:
                registrar(usuario)
            usuario.delete()
    except ProtectedError:
        raise GestionUsuarioError(
            "No se puede rechazar: la cuenta tiene historial protegido."
        ) from None
    transaction.on_commit(partial(notificaciones.avisar_rechazo, nombre, email))
    return True


def resolver_panel(request, usuario_id, operacion, version, *, original=None):
    with bloquear(request, [usuario_id]) as filas:
        usuario = filas.get(usuario_id)
        if usuario is None:
            raise GestionUsuarioError("La cuenta ya no está disponible.")
        if usuario.aprobada and (usuario.version_administrativa != version or original is not None):
            raise GestionUsuarioError("La cuenta ya no está pendiente.")
        comprobar_revision(usuario, version, original)
        return _resolver(request, usuario, operacion)


def aprobar_solicitud_panel(request, usuario_id, version, *, original=None):
    return resolver_panel(request, usuario_id, "aprobar", version, original=original)


def rechazar_solicitud_panel(request, usuario_id, version, *, original=None):
    return resolver_panel(request, usuario_id, "rechazar", version, original=original)


def resolver_solicitudes_admin(request, objetivos, operacion, *, originales=None, registrar=None):
    accion = "delete" if operacion == "rechazar" else "change"
    with bloquear(request, objetivos, canal="admin", accion=accion) as filas:
        if originales is not None:
            for pk in objetivos:
                usuario = filas.get(pk)
                original = originales.get(str(pk))
                if usuario is None or original is None:
                    raise GestionUsuarioError("La selección cambió. Revisá nuevamente.")
                comprobar_revision(usuario, original["version"], original)
        cantidad, errores = 0, []
        for pk in sorted(set(objetivos)):
            usuario = filas.get(pk)
            if usuario is None:
                continue
            try:
                cantidad += _resolver(request, usuario, operacion, registrar)
            except GestionUsuarioError as exc:
                errores.append(f"{usuario.email}: {exc}")
        return cantidad, errores


def cambiar_estado_panel(request, usuario_id, activa, version, *, original=None):
    if type(activa) is not bool:
        raise GestionUsuarioError("Estado inválido.")
    with bloquear(request, [usuario_id]) as filas:
        usuario = filas.get(usuario_id)
        if usuario is None:
            raise GestionUsuarioError("La cuenta ya no está disponible.")
        comprobar_revision(usuario, version, original)
        if not usuario.aprobada:
            raise GestionUsuarioError("Las pendientes se gestionan desde Solicitudes de cuenta.")
        return _estado(request, usuario, activa)


def cambiar_rol_panel(request, usuario_id, bioquimico, version, *, original=None):
    if type(bioquimico) is not bool:
        raise GestionUsuarioError("Rol inválido.")
    with bloquear(request, [usuario_id]) as filas:
        usuario = filas.get(usuario_id)
        if usuario is None:
            raise GestionUsuarioError("La cuenta ya no está disponible.")
        comprobar_revision(usuario, version, original)
        if not usuario.aprobada:
            raise GestionUsuarioError("Las pendientes se gestionan desde Solicitudes de cuenta.")
        grupo = Group.objects.get(name="Bioquímicos")
        if usuario.groups.filter(pk=grupo.pk).exists() == bioquimico:
            return False
        if bioquimico:
            usuario.groups.add(grupo)
        else:
            usuario.groups.remove(grupo)
        usuario.version_administrativa += 1
        usuario.save(update_fields=["version_administrativa"])
        return True


def guardar_cuenta_admin(request, propuesta, version, original, campos):
    """Guarda valores validados sobre una instancia recargada, nunca la del binding."""
    with bloquear(request, [propuesta.pk], canal="admin") as filas:
        vigente = filas.get(propuesta.pk)
        if vigente is None:
            raise GestionUsuarioError("La cuenta ya no está disponible.")
        comprobar_revision(vigente, version, original)
        # La transición común se aplica en memoria y se persiste en una sola escritura.
        cambio = False
        activa = propuesta.is_active if "is_active" in campos else vigente.is_active
        cambio |= activa != vigente.is_active
        aprobar = _preparar_estado(request, vigente, activa)
        for campo in campos:
            if campo == "is_active":
                continue
            valor = getattr(propuesta, campo)
            cambio |= getattr(vigente, campo) != valor
            setattr(vigente, campo, valor)
        vigente.version_administrativa += bool(cambio)
        vigente.save()
        if aprobar:
            _avisar_aprobacion(request, vigente)
        return vigente
