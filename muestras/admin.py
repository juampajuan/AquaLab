from django.contrib import admin

from .models import Muestra, Origen


@admin.register(Origen)
class OrigenAdmin(admin.ModelAdmin):
    list_display = ("nombre", "cliente", "fecha_alta")
    search_fields = ("nombre", "cliente__razon_social", "cliente__nombre")
    readonly_fields = ("fecha_alta",)


@admin.register(Muestra)
class MuestraAdmin(admin.ModelAdmin):
    """Solo consulta: el alta es por la pantalla de la US 4.1 y editar o desactivar queda fuera."""

    list_display = (
        "numero_pi",
        "nombre",
        "cliente",
        "origen",
        "fecha_ingreso",
        "tipo_vertido",
        "estado",
        "registrada_por",
        "fecha_registro",
    )
    list_filter = ("tipo_vertido", "estado")
    search_fields = (
        "numero_pi",
        "nombre",
        "cliente__razon_social",
        "cliente__nombre",
        "origen__nombre",
    )
    readonly_fields = ("numero_pi", "estado", "registrada_por", "fecha_registro")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
