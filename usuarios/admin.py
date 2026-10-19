from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

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
    actions = ["aprobar_cuentas"]
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
        aprobadas = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(request, f"Se aprobaron {aprobadas} cuenta(s).", messages.SUCCESS)
