from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_completo",
        "tipo_documento",
        "numero_documento",
        "email",
        "telefono",
        "activo",
        "fecha_alta",
    )
    list_filter = ("tipo_documento", "activo")
    search_fields = ("nombre", "razon_social", "numero_documento", "email")
    readonly_fields = ("fecha_alta",)
    ordering = ("-fecha_alta",)
