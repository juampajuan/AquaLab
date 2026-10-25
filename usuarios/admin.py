from functools import partial

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db import transaction
from django.template.response import TemplateResponse

from . import notificaciones
from .forms import UsuarioChangeForm, UsuarioCreationForm
from .models import Usuario


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
        ("Estado", {"fields": ("is_active",)}),
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

    @admin.action(description="Aprobar cuentas seleccionadas", permissions=["change"])
    def aprobar_cuentas(self, request, queryset):
        with transaction.atomic():
            # El bloqueo hace que dos aprobaciones simultáneas no avisen dos veces.
            pendientes = list(queryset.filter(is_active=False).select_for_update())
            Usuario.objects.filter(pk__in=[u.pk for u in pendientes]).update(is_active=True)
            for usuario in pendientes:
                transaction.on_commit(partial(notificaciones.avisar_aprobacion, request, usuario))
        self.message_user(request, f"Se aprobaron {len(pendientes)} cuenta(s).", messages.SUCCESS)

    @admin.action(description="Rechazar solicitudes seleccionadas", permissions=["delete"])
    def rechazar_solicitudes(self, request, queryset):
        if request.POST.get("confirmar") != "si":
            pendientes = queryset.filter(is_active=False)
            if not pendientes.exists():
                self.message_user(
                    request, "No hay solicitudes pendientes en la selección.", messages.WARNING
                )
                return None
            contexto = {
                **self.admin_site.each_context(request),
                "title": "Rechazar solicitudes",
                "pendientes": pendientes,
                "hay_aprobadas": queryset.filter(is_active=True).exists(),
                "opts": self.model._meta,
            }
            return TemplateResponse(
                request, "admin/usuarios/usuario/rechazar_confirmacion.html", contexto
            )

        with transaction.atomic():
            pendientes = list(queryset.filter(is_active=False).select_for_update())
            rechazados = [(u.first_name, u.email) for u in pendientes]
            if pendientes:
                a_eliminar = Usuario.objects.filter(pk__in=[u.pk for u in pendientes])
                self.log_deletions(request, a_eliminar)
                a_eliminar.delete()
            for nombre, email in rechazados:
                transaction.on_commit(partial(notificaciones.avisar_rechazo, nombre, email))
        self.message_user(
            request, f"Se rechazaron {len(rechazados)} solicitud(es).", messages.SUCCESS
        )
        return None

    def save_model(self, request, obj, form, change):
        estaba_pendiente = (
            change
            and Usuario.objects.select_for_update().filter(pk=obj.pk, is_active=False).exists()
        )
        super().save_model(request, obj, form, change)
        if estaba_pendiente and obj.is_active:
            transaction.on_commit(partial(notificaciones.avisar_aprobacion, request, obj))
