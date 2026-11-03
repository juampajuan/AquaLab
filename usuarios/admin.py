from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import UserAdmin
from django.core import signing
from django.template.response import TemplateResponse

from . import confirmaciones_administracion as confirmaciones
from .forms import UsuarioChangeForm, UsuarioCreationForm
from .models import Usuario
from .servicios_administracion import (
    GestionUsuarioError,
    bloquear,
    guardar_cuenta_admin,
    instantanea,
    resolver_solicitudes_admin,
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    form = UsuarioChangeForm
    add_form = UsuarioCreationForm
    list_display = ("email", "first_name", "last_name", "is_active", "date_joined")
    list_filter = ("is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
    actions = ["aprobar_cuentas", "rechazar_solicitudes"]
    fieldsets = (
        ("Datos personales", {"fields": ("email", "first_name", "last_name")}),
        ("Contraseña", {"fields": ("password",)}),
        ("Estado", {"fields": ("is_active", "contexto_administrativo")}),
        ("Permisos", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        base = super().get_form(request, obj, **kwargs)
        if obj is None:
            return base

        class FichaConRequest(base):
            def __init__(self, *args, **opciones):
                super().__init__(*args, request=request, **opciones)

        return FichaConRequest

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if request.method == "POST" and object_id is not None:
            try:
                pk = int(unquote(object_id))
            except ValueError:
                return super().changeform_view(request, object_id, form_url, extra_context)
            with bloquear(request, [pk], canal="admin"):
                return super().changeform_view(request, object_id, form_url, extra_context)
        return super().changeform_view(request, object_id, form_url, extra_context)

    @admin.action(description="Aprobar cuentas seleccionadas", permissions=["change"])
    def aprobar_cuentas(self, request, queryset):
        cantidad, errores = resolver_solicitudes_admin(
            request, list(queryset.values_list("pk", flat=True)), "aprobar"
        )
        self.message_user(request, f"Se aprobaron {cantidad} cuenta(s).", messages.SUCCESS)
        for error in errores:
            self.message_user(request, error, messages.ERROR)

    @admin.action(description="Rechazar solicitudes seleccionadas", permissions=["delete"])
    def rechazar_solicitudes(self, request, queryset):
        if request.POST.get("confirmar") != "si":
            pendientes = list(queryset.filter(aprobada=False, is_active=False))
            if not pendientes:
                self.message_user(
                    request, "No hay solicitudes pendientes en la selección.", messages.WARNING
                )
                return None
            originales = {str(u.pk): instantanea(u) for u in pendientes}
            contexto = {
                **self.admin_site.each_context(request),
                "title": "Rechazar solicitudes",
                "pendientes": pendientes,
                "hay_aprobadas": queryset.filter(aprobada=True).exists(),
                "opts": self.model._meta,
                "contexto_administrativo": confirmaciones.firmar_ficha(
                    request, originales, operacion="rechazar"
                ),
            }
            return TemplateResponse(
                request, "admin/usuarios/usuario/rechazar_confirmacion.html", contexto
            )
        try:
            originales = confirmaciones.leer_ficha(
                request, request.POST.get("contexto_administrativo", ""), operacion="rechazar"
            )
            objetivos = list(queryset.values_list("pk", flat=True))
            if set(originales) != {str(pk) for pk in objetivos}:
                raise GestionUsuarioError("La selección cambió. Revisá nuevamente.")
            cantidad, errores = resolver_solicitudes_admin(
                request,
                objetivos,
                "rechazar",
                originales=originales,
                registrar=lambda usuario: self.log_deletions(request, [usuario]),
            )
        except (signing.BadSignature, GestionUsuarioError):
            self.message_user(
                request, "La confirmación cambió o es inválida. Revisá nuevamente.", messages.ERROR
            )
            return None
        self.message_user(request, f"Se rechazaron {cantidad} solicitud(es).", messages.SUCCESS)
        for error in errores:
            self.message_user(request, error, messages.ERROR)
        return None

    def save_model(self, request, obj, form, change):
        if not change:
            return super().save_model(request, obj, form, change)
        original = form.original_firmado
        campos = [
            campo.name
            for campo in self.model._meta.concrete_fields
            if campo.editable and not campo.primary_key and campo.name in form.changed_data
        ]
        vigente = guardar_cuenta_admin(request, obj, original["version"], original, campos)
        for campo in self.model._meta.concrete_fields:
            setattr(obj, campo.attname, getattr(vigente, campo.attname))

    def save_related(self, request, form, formsets, change):
        anterior = instantanea(form.instance) if change else None
        super().save_related(request, form, formsets, change)
        if change:
            despues = instantanea(form.instance)
            if any(anterior[k] != despues[k] for k in ("grupos", "permisos")):
                form.instance.version_administrativa += 1
                form.instance.save(update_fields=["version_administrativa"])

    def user_change_password(self, request, id, form_url=""):
        if request.method != "POST":
            return super().user_change_password(request, id, form_url)
        try:
            pk = int(unquote(id))
        except ValueError:
            return super().user_change_password(request, id, form_url)
        with bloquear(request, [pk], canal="admin") as filas:
            respuesta = super().user_change_password(request, id, form_url)
            if respuesta.status_code == 302 and pk in filas:
                usuario = filas[pk]
                usuario.version_administrativa += 1
                usuario.save(update_fields=["version_administrativa"])
            return respuesta
